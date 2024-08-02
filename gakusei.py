###############################################################################
#                                                                             #
#           GAKUSEI - An Old School Go/Weiqi/Baduk playing program            #
#                                                                             #
###############################################################################

# GLOBAL CONSTANTS
NONE = -1                   # value of not initialized variable
EMPTY = 0                   # blanc board square value
BLACK = 1                   # value of board square occupied by black stone
WHITE = 2                   # value of board square occupied by white stone
FENCE = 3                   # offboard value
ESCAPE = 4                  # liberty mask value

# GLOBAL VARIABLES
width = NONE                # board width (9, 13, 19 or other)
board = [[]]                # board position, two dimensional array
side = NONE                 # side to move, either BLACK or WHITE
ko = [NONE, NONE]           # Ko square, cannot place a stone on it
groups = []                 # black and white groups database

def init_board(size):
  global width, board, side, ko, groups
  '''
  Initializes board array of a given size with zeros,
  sets the side to move, resets a Ko square,
  clears groups database
  '''
  width = size+2 # add offboard squares
  board = [[0 for _ in range(width)] for _ in range(width)]
  for row in range(width):
    for col in range(width):
      if row == 0 or row == width-1 or col == 0 or col == width-1:
        board[row][col] = FENCE
  side = BLACK
  ko = [NONE, NONE]
  groups = [set(), set()]

def print_board():
  '''
  Prints the board and game state to STDOUT,
  used for debugging and by GTP command "showboard"
  '''
  for row in range(width):
    for col in range(width):
      if col == 0 and row != 0 and row != width-1:
        rown = width-row-1
        print((' ' if rown < 10 else ''), rown, end='  ')
      if board[row][col] == FENCE: continue
      if row == ko[0] and col == ko[1]: print('#', end=' ')
      else: print(['.', 'X', 'O', '#'][board[row][col]], end=' ')
    print()
  print('    ', 'A B C D E F G H J K L M N O P Q R S T'[:width*2-4])
  print('\n     Side to move:', ('BLACK' if side == 1 else 'WHITE'))
  print('\n')

def count(col, row, color, marks):
  '''
  Finds all stones of a given color connected to to the
  current stone at board[row][col], marks stones and liberties
  in a corresponding array which is essentially a helper board
  '''
  stone = board[row][col]
  if stone == FENCE: return
  if stone and (stone & color) and marks[row][col] == EMPTY:
    marks[row][col] = stone
    count(col+1, row, color, marks)
    count(col-1, row, color, marks)
    count(col, row+1, color, marks)
    count(col, row-1, color, marks)
  elif stone == EMPTY:
    marks[row][col] = ESCAPE

def add_stones(marks, color):
  global groups
  '''
  Extracts stone/liberty coordinates and stores them to groups
  '''
  groups = [set(), set()]
  stones = set()
  liberties = set()
  for row in range(width):
    for col in range(width):
      stone = marks[row][col]
      if stone == FENCE or stone == EMPTY: continue
      if stone == ESCAPE: liberties.add((col, row))
      else: stones.add((col, row))
  groups[color-1].add((frozenset(stones), frozenset(liberties)))


def update_groups():
  '''
  Keeps track of BLACK and WHITE groups on board by
  maintaining coordinates of stones and their liberties
  '''
  marks = [[EMPTY for _ in range(width)] for _ in range(width)]
  for row in range(width):
    for col in range(width):
      stone = board[row][col]
      if stone == FENCE or stone == EMPTY: continue
      count(col, row, BLACK, marks)
      add_stones(marks, BLACK)
  [print(i) for i in marks]

init_board(9)
board = [
  [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
  [3, 0, 0, 0, 1, 0, 0, 0, 0, 0, 3],
  [3, 0, 0, 2, 1, 0, 1, 1, 1, 0, 3],
  [3, 0, 2, 1, 1, 0, 0, 0, 0, 0, 3],
  [3, 0, 0, 1, 2, 2, 0, 0, 1, 0, 3],
  [3, 0, 0, 1, 0, 2, 0, 2, 0, 0, 3],
  [3, 0, 0, 0, 0, 2, 2, 2, 0, 0, 3],
  [3, 0, 0, 0, 0, 2, 0, 2, 0, 0, 3],
  [3, 0, 0, 0, 0, 2, 2, 2, 0, 0, 3],
  [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
  [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
]
print_board()
update_groups()

