Minisat-Based Sudoku Solver
===========================

This is a simple Sudoku solver which solves puzzles from http://dailysudoku.com.
The motivation for creating this came from Homework 8 of EECS 376.
I apologize for lack of documentation, it was thrown together pretty quickly.


Command line usage
-----
`$ ./solver.py <input-file> (output-pdf)`

Input files may be either ASCII or PDF (in forms found on dailysudoku.com).
The program is also capable of outputting a solved PDF, as long as the original input was also a PDF.

As a Library
------------
    >>> from solver import Sudoku
    >>> p = """
            +-------+-------+-------+
            | . . . | . . 8 | . 5 4 |
            | . . 5 | . . 3 | 1 6 . |
            | 8 . . | 4 . . | 3 2 . |
            +-------+-------+-------+
            | 5 . . | 6 . . | 4 3 . |
            | 7 8 4 | . . . | 9 1 6 |
            | . 9 6 | . . 1 | . . 5 |
            +-------+-------+-------+
            | . 5 7 | . . 4 | . . 1 |
            | . 2 8 | 9 . . | 6 . . |
            | 1 3 . | 8 . . | . . . |
            +-------+-------+-------+
            """
    >>> s = Sudoku(p)
    >>> sol = s.solve()
    >>> print sol.ascii()
    +-------+-------+-------+
    | 2 6 3 | 1 9 8 | 7 5 4 |
    | 9 4 5 | 2 7 3 | 1 6 8 |
    | 8 7 1 | 4 5 6 | 3 2 9 |
    | 5 1 2 | 6 8 9 | 4 3 7 |
    | 7 8 4 | 5 3 2 | 9 1 6 |
    | 3 9 6 | 7 4 1 | 2 8 5 |
    | 6 5 7 | 3 2 4 | 8 9 1 |
    | 4 2 8 | 9 1 5 | 6 7 3 |
    | 1 3 9 | 8 6 7 | 5 4 2 |
    +-------+-------+-------+

The relevant DIMACS string can also be generated as follows:
`>>> dimacs = s.get_dimacs()`
