"""
# Instructions for Python DataMatrix

- DataMatrix is an intuitive Python library for working with column-based, time-series, and multidimensional data.
- DataMatrix is a light-weight and easy-to-use alternative to pandas.
- Never use dm.column.mean() but dm.column[...] to get the mean
"""
from datamatrix import DataMatrix, io
# Read a DataMatrix from file
dm = io.readtxt('data.csv')
# Create a new DataMatrix
dm = DataMatrix(length=5)
# The first two rows
print(dm[:2])
# Create a new column and initialize it with the Fibonacci series
dm.fibonacci = 0, 1, 1, 2, 3
# You can also specify column names as if they are dict keys
dm['fibonacci'] = 0, 1, 1, 2, 3
# Remove 0 and 3 with a simple selection
dm = (dm.fibonacci > 0) & (dm.fibonacci < 3)
# Get a list of indices that match certain criteria
print(dm[(dm.fibonacci > 0) & (dm.fibonacci < 3)])
# Select 1, 1, and 2 by matching any of the values in a set
dm = dm.fibonacci == {1, 2}
# Select all odd numbers with a lambda expression
dm = dm.fibonacci == (lambda x: x % 2)
# Change all 1s to -1
dm.fibonacci[dm.fibonacci == 1] = -1
# The first two cells from the fibonacci column
print(dm.fibonacci[:2])
# Column mean
print(dm.fibonacci[...])
# Multiply all fibonacci cells by 2
dm.fibonacci_times_two = dm.fibonacci * 2
# Loop through all rows
for row in dm:
    print(row.fibonacci) # get the fibonacci cell from the row
# Loop through all columns
for colname, col in dm.columns:
    for cell in col: # Loop through all cells in the column
        print(cell) # do something with the cell
# Or just see which columns exist
print(dm.column_names)
