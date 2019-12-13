CC=gcc
CFLAGS=-fPIC -shared -O2 -std=c99 -Wall -Werror

all: heatmap 
clean: clean_heatmap

heatmap: util/_cmap.so

util/_cmap.so: util/_cmap.c
	$(CC) $(CFLAGS) $< -o $@

clean_heatmap:
	rm util/_cmap.so

