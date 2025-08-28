/*
 * Simple sorting program for ARMv7 cross-compilation demonstration
 * 
 * This program implements quicksort algorithm to sort an array of integers.
 * Time complexity: O(n log n) average case, O(n²) worst case
 * Space complexity: O(log n) average case due to recursion stack
 */

#include <stdio.h>
#include <stdlib.h>

#define ARRAY_SIZE 10

/* Function prototypes */
void quicksort(int arr[], int low, int high);
int partition(int arr[], int low, int high);
void swap(int *a, int *b);
void print_array(const int arr[], int size);

/*
 * Swap two integers
 */
void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

/*
 * Partition function for quicksort
 * Places pivot in correct position and returns its index
 */
int partition(int arr[], int low, int high) {
    int pivot = arr[high];  /* Choose last element as pivot */
    int i = (low - 1);      /* Index of smaller element */
    
    for (int j = low; j <= high - 1; j++) {
        /* If current element is smaller than or equal to pivot */
        if (arr[j] <= pivot) {
            i++;    /* increment index of smaller element */
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return (i + 1);
}

/*
 * Quicksort implementation
 * Recursively sorts array elements
 */
void quicksort(int arr[], int low, int high) {
    if (low < high) {
        /* Partition the array and get pivot index */
        int pi = partition(arr, low, high);
        
        /* Recursively sort elements before and after partition */
        quicksort(arr, low, pi - 1);
        quicksort(arr, pi + 1, high);
    }
}

/*
 * Print array elements
 */
void print_array(const int arr[], int size) {
    for (int i = 0; i < size; i++) {
        printf("%d", arr[i]);
        if (i < size - 1) {
            printf(", ");
        }
    }
    printf("\n");
}

/*
 * Main function
 */
int main(void) {
    /* Static array with unsorted data */
    int data[ARRAY_SIZE] = {64, 34, 25, 12, 22, 11, 90, 88, 76, 50};
    
    printf("ARM Cross-Compilation Sorting Demo\n");
    printf("Algorithm: Quicksort\n");
    printf("Array size: %d\n\n", ARRAY_SIZE);
    
    printf("Original array: ");
    print_array(data, ARRAY_SIZE);
    
    /* Sort the array */
    quicksort(data, 0, ARRAY_SIZE - 1);
    
    printf("Sorted array:   ");
    print_array(data, ARRAY_SIZE);
    
    printf("\nSorting completed successfully!\n");
    
    return 0;
}