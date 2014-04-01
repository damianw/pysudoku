#!/usr/bin/env python

import re
import operator
import fileinput
from time import time
from copy import deepcopy
from pprint import pprint
from satispy.io import DimacsCnf
from satispy import Variable, Cnf
from satispy.solver import Minisat

class SudokuVar(Variable):
  def __init__(self, name, row, col, val):
    super(SudokuVar, self).__init__(name)
    self.row = row
    self.col = col
    self.val = val

class Sudoku:

  def __init__(self, pstring):
    pstring = pstring.strip()
    self.pdf = None
    if pstring.startswith("%PDF-1.2"):
      self.grid = self._parsepdf(pstring)
      self.pdf = [line for line in pstring.splitlines() if not line.startswith(" BT /F1 20.00 Tf")]
    elif pstring.startswith(("+" + "-" * 7) * 3 + "+\n"):
      self.grid = self._parsegrid(pstring)
    else:
      raise ValueError("Only PDF and ASCII inputs are supported!")

  def cnf(self):
    return Sudoku._gen_expr(self.grid)

  def get_sat_solution(self):
    solver = Minisat()
    solution = solver.solve(self.cnf())
    return solution

  def solve(self):
    sol = self.get_sat_solution()
    flat = sum(Sudoku._gen_matrix(), [])
    flat = sum(flat, [])
    variables = [var for var in flat if sol[var] == True]
    board = deepcopy(self.grid)
    for var in variables:
      board[var.row][var.col] = var.val
    return Solution(board, self.pdf)

  def brute_force(self):
    fields = list(Sudoku._get_fields(self.grid))
    print "%d possible solutions!" % (9 ** (len(fields)))
    print "This is going to take a really... REALLY long time."
    board = deepcopy(self.grid)
    global attempt
    attempt = 1
    def _bf_helper(grid, fields, i):
      global attempt
      if i < len(fields):
        coords = fields[i]
        for val in xrange(1,10):
          grid[coords[0]][coords[1]] = val
          print "\rAttempt: %d" % attempt,
          if Sudoku._is_solution(grid):
            return True
          if _bf_helper(grid, fields, i+1) == True:
            return True
      attempt += 1
      return False
    success = _bf_helper(board, fields, 0)
    return Solution(board, self.pdf)

  @staticmethod 
  def _parsepdf(pstring):
    lines = [line.strip().split() for line in pstring.splitlines() if line.startswith(" BT /F1 20.00 Tf")]
    vals = [(line[4], line[5], line[7].strip('()'),) for line in lines]
    grid = [[0]*9 for x in xrange(9)]
    for val in vals:
      (row, col) = Solution._xy_to_rc(float(val[0]), float(val[1]))
      grid[int(row)][int(col)] = int(val[2])
    return grid

  @staticmethod 
  def _is_solution(grid):
    horiz = [Sudoku._uniques(row) for row in grid]
    vert = [Sudoku._uniques(col) for col in Sudoku._get_cols(grid)]
    boxes = [sum(Sudoku._get_box(grid, row*3, col*3), []) for row in xrange(2) for col in xrange(2)]
    box = [Sudoku._uniques(box) for box in boxes]
    return reduce(operator.and_, horiz + vert + box)

  @staticmethod
  def _uniques(l):
    return reduce(operator.and_, [l.count(n) == 1 for n in xrange(1,10)])

  @staticmethod 
  def _get_cols(grid):
    for i in xrange(9):
      yield [row[i] for row in grid]

  def get_dimacs(self):
    return str(DimacsCnf().tostring(self.cnf()))

  @staticmethod
  def _get_fields(grid):
    for row in xrange(9):
      for col in xrange(9):
        if grid[row][col] == 0:
          yield (row,col,)

  @staticmethod
  def _chunks(l, n):
    "Yield successive n-sized chunks from l."
    for i in xrange(0, len(l), n):
      yield l[i:i+n]

  @staticmethod
  def _parsegrid(pstring):
    "Returns a 2D array representing the puzzle."
    cells = [int(n) for n in re.findall(r'[0-9]', pstring.replace('.', '0'))]
    return list(Sudoku._chunks(cells, 9))

  @staticmethod 
  def _gen_expr(grid):
    result = Sudoku._gen_base_expr()
    matrix = Sudoku._gen_matrix()
    # start with row constraints
    for rownum in xrange(9):
      for colnum in xrange(9):
        val = grid[rownum][colnum]
        if val != 0:
          result &= matrix[rownum][colnum][val-1]
    return result

  @staticmethod
  def _gen_base_expr():
    matrix = Sudoku._gen_matrix()
    result = Cnf()
    # every cell must be included
    for row in matrix:
      for cell in row:
        temp = Cnf()
        for option in cell:
          temp |= option
        result &= temp
    # row constraints
    for row in matrix:
      for cell in row:
        for other in [thing for thing in row if thing is not cell]:
          for i in xrange(9):
            result &= -(cell[i] & other[i])
    # column constraints
    for colnum in xrange(9):
      for rownum in xrange(9):
        cell = matrix[rownum][colnum]
        for otherrow in [n for n in xrange(9) if n != rownum]:
          other = matrix[otherrow][colnum]
          for i in xrange(9):
            result &= -(cell[i] & other[i])
    # box constraints
    for rownum in xrange(9):
      for colnum in xrange(9):
        cell = matrix[rownum][colnum]
        for orow in Sudoku._get_box(matrix, rownum, colnum):
          for other in [thing for thing in orow if thing is not cell]:
            for i in xrange(9):
              result &= -(cell[i] & other[i])
    # it's so crazy it just might work
    return result

  @staticmethod 
  def _get_box(matrix, row, col):
    rdex = (row / 3) * 3
    cdex = (col / 3) * 3
    return [item[cdex:cdex+3] for item in matrix[rdex:rdex+3]]

  @staticmethod 
  def _gen_matrix():
    return [[[SudokuVar("(%d,%d)=%d" % (row, col, val), row, col, val) for val in xrange(1,10)] for col in xrange(9)] for row in xrange(9)]

class Solution:
  def __init__(self, grid, pdf=None):
    self.grid = grid
    self.mpdf = pdf

  def ascii(self):
    result = ("+" + "-" * 7) * 3 + "+\n"
    for row in self.grid:
      for chunk in Sudoku._chunks(row, 3):
        result += "| "
        for cell in chunk:
          result += "%d " % cell
      result += "|\n"
    result += ("+" + "-" * 7) * 3 + ("+")
    return result

  def pdf(self):
    if self.mpdf is None:
      raise "PDF output requires PDF input!"
    return '\n'.join(self._fill_pdf(self.grid, self.mpdf))

  @staticmethod
  def _fill_pdf(grid, pdf):
    front = pdf[:67]
    back = pdf[67:]
    for entry in Solution._gen_pdfentries(grid):
      front.append(entry)
    return front + back 

  @staticmethod
  def _gen_pdfentries(grid):
    for r in xrange(9):
      for c in xrange(9):
        (x, y) = Solution._rc_to_xy(r, c)
        yield "BT /F1 20.00 Tf {0} {1} Td ({2}) Tj ET".format(x, y, grid[r][c])

  @staticmethod
  def _xy_to_rc(x, y):
    STARTX = 189.45
    STARTY = 698
    DELTA = 30
    row = (STARTY - y) / DELTA
    col = (x - STARTX) / DELTA
    return (int(row), int(col),)

  @staticmethod 
  def _rc_to_xy(row, col):
    STARTX = 189.45
    STARTY = 698
    DELTA = 30
    x = col * DELTA + STARTX
    y = STARTY - row * DELTA
    return (x, y,)

if __name__ == "__main__":
  from sys import argv
  with open(argv[1], 'r') as f:
    pstring = f.read()
  s = Sudoku(pstring)
  sol = s.solve()
  print sol.ascii()
  if len(argv) == 3:
    with open(argv[2], 'w') as f:
      f.write(sol.pdf())