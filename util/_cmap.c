/* This file is (c) 2013 Richard Barrell <rchrd@brrll.co.uk>, see LICENSE.txt */
/* (it's the ISC license, which is 2-clause BSD with simplified wording) */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>


typedef struct {
    int32_t x;
    int32_t y;
} pair;


/* This struct defines a circular queue. */
typedef struct {
    /* Pointer to the beginning of the block of memory containing all of the 
     * elements in the queue. */
    pair *pairs;
    size_t size; // Number of elements in the queue
    size_t head; // Index of first element in the queue
    size_t tail; // Index *after* last element in the queue
} queue;


/* Start a new queue */
static int initQueue(queue *q)
{
    q->pairs = (pair*) malloc(sizeof(pair));
    if (q->pairs == NULL) {
        /* Memory allocation failed */
        return -1;
    }
    q->size = 1;
    q->head = 0;
    q->tail = 0;
    return 0;
}


/* Clean up memory used by the queue */
static void freeQueue(queue *q) {
    free(q->pairs);
}


/* Return the number of elements in the queue. */
static size_t getNumElements(queue *q) {
    size_t gap = q->tail - q->head;
    if (q->head > q->tail) {
        gap += q->size;
    }
    return gap;
}


/* Given a pair, insert it into the queue */
static int addToQueue(queue *q, pair p) {
    if ((getNumElements(q) + 1) == q->size) {
        /* Adding this pair would put us over the size limit, so we need
         * to make more room. Allocate double the old memory used. */
        size_t oldSize = q->size;
        q->size = q->size * 2;
        q->pairs = (pair*) realloc(q->pairs, q->size * sizeof(pair));
        if (q->pairs == NULL) {
            /* Memory allocation failed */
            return -1;
        }
        if (q->tail < q->head) {
            /* The active contents of the queue "wrapped around" the end of
             * the ring; shuffle things around so that the bits before
             * and after the wrap are now contiguous.
             * (BBB***AA) -> (***********AABBB)
             */
            memcpy(q->pairs + oldSize, q->pairs, q->tail * sizeof(pair));
            q->tail = oldSize + q->tail;
        }
    }
    if (q->tail == q->size) {
        /* Hit the end of the queue; start wrapping around */
        q->tail = 0;
    }
    q->pairs[q->tail] = p;
    q->tail++;
    return 0;
}


/* Remove the oldest element from the queue and return it */
static pair queuePopLeft(queue *q) {
    size_t oldHead = q->head;
    q->head = q->head + 1;
    if (q->head == q->size) {
        q->head = 0;
        // Special case: if tail had been sitting past the end of the queue,
        // then we now need to recognize this; otherwise getNumElements will
        // think there's still things in the queue.
        if (q->tail == q->size) {
            q->tail = 0;
        }
    }
    return q->pairs[oldHead];
}


static int getbit(uint8_t *u, int32_t x, int32_t y, int32_t xMax) {
    int32_t pos = y*xMax + x;
    int32_t pos_byte = pos >> 3;
    int32_t pos_bit  = pos & 0x7;
    int val = (u[pos_byte] >> pos_bit) & 0x1;
    return val;
}


static void setbit(uint8_t *u, int32_t x, int32_t y, int32_t xMax) {
    int32_t pos = y*xMax + x;
    int32_t pos_byte = pos >> 3;
    int32_t pos_bit  = pos & 0x7;
    uint8_t bit = 1 << pos_bit;
    u[pos_byte] = (u[pos_byte] & ~bit) | bit;
}


int burnHeatMap(int32_t xMax, int32_t yMax,
        int32_t *heatMap,
        size_t goals_length, int32_t *goalXs, int32_t *goalYs)
{
    int failLine = 0;

    size_t numCells = xMax * yMax;
    uint8_t *usedCells = (uint8_t*) calloc(numCells, 1);

    queue cellQueue;
    if (initQueue(&cellQueue) != 0) {
        // Allocating memory for the queue failed.
        failLine = __LINE__ || -1;
        goto cleanup_none;
    }

    if (usedCells == NULL) {
        // Allocating memory for the used-cells array failed.
        failLine = __LINE__ || -1;
        goto cleanup_queue;
    }

#define IX(x, y) heatMap[(y)*xMax + (x)]
#define GETUSED(x, y) getbit(usedCells, (x), (y), xMax)
#define SETUSED(x, y) setbit(usedCells, (x), (y), xMax)
#define MAX(a,b) ((a)>(b)?(a):(b))
#define MIN(a,b) ((a)<(b)?(a):(b))

    // Initialize the used-cells array
    for (int32_t y = 0; y < yMax; y++) {
        for (int32_t x = 0; x < xMax; x++) {
            if (IX(x, y) != 0) {
                SETUSED(x, y);
            }
            IX(x, y) = -1;
        }
    }

    // Initialize the goals with cost 0, and add their neighbors to the 
    // queue.
    for (size_t i = 0; i < goals_length; i++) {
        int32_t x = goalXs[i], y = goalYs[i];
        IX(x, y) = 0;
        SETUSED(x, y);
        pair xy = {x, y};
        if (addToQueue(&cellQueue, xy) != 0) {
            failLine = __LINE__ || -1;
            goto cleanup_getNumElements;
        }
    }

    // Pop elements off the queue, find unused neighbors, record their costs,
    // and add them to the queue.
    while (getNumElements(&cellQueue) > 0) {
        pair xy = queuePopLeft(&cellQueue);
        int32_t x = xy.x, y = xy.y;
        int32_t cost = IX(x, y);
        for (int32_t yi = MAX(0, y - 1); yi < MIN(yMax, y + 2); yi++) {
            for (int32_t xi = MAX(0, x - 1); xi < MIN(xMax, x + 2); xi++) {
                if ((x == xi && y == yi) || GETUSED(xi, yi)) {
                    // "Neighbor" is in fact us, or neighbor has already been
                    // used.
                    continue;
                }
                SETUSED(xi, yi);
                IX(xi, yi) = cost + 1;
                pair xiyi = {xi, yi};
                if (addToQueue(&cellQueue, xiyi) != 0) {
                    // Failed to add neighbor to the queue.
                    failLine = __LINE__ || -1;
                    goto cleanup_getNumElements;
                }
            }
        }
    }

   cleanup_getNumElements:
      free(usedCells);
   cleanup_queue:
      freeQueue(&cellQueue);
   cleanup_none:
      return failLine;
}

