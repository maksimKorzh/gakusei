###############################################################################
#                                                                             #
#           GAKUSEI - An Old School Go/Weiqi/Baduk playing program            #
#                                                                             #
###############################################################################

import sys

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
ko = [NONE, NONE]           # [col, row] Ko square, cannot set a stone on it
groups = []                 # black and white groups database

def init_board():
  global board, side, ko, groups
  '''
  Initializes board array of a given size with zeros,
  sets the side to move, resets a Ko square,
  clears groups database
  '''
  board = [[0 for _ in range(width)] for _ in range(width)]
  for row in range(width):
    for col in range(width):
      if row == 0 or row == width-1 or col == 0 or col == width-1:
        board[row][col] = FENCE
  side = BLACK
  ko = [NONE, NONE]
  groups = [[], []]

def print_board():
  '''
  Prints the board and game state to STDOUT,
  used for debugging and by GTP command "showboard"
  '''
  for row in range(width):
    for col in range(width):
      if col == 0 and row != 0 and row != width-1:
        rown = width-row-1
        print((' ' if rown < 10 else ''), rown, end=' ')
      if board[row][col] == FENCE: continue
      if col == ko[0] and row == ko[1]: print('#', end=' ')
      else: print(['.', 'X', 'O', '#'][board[row][col]], end=' ')
    if row < width-1: print()
  print('   ', 'A B C D E F G H J K L M N O P Q R S T'[:width*2-4])
  print('\n    Side to move:', ('BLACK' if side == 1 else 'WHITE'))
  print()
  print('    Black groups:')
  for group in groups[BLACK-1]: print('      ', group)
  print('\n    White groups:')
  for group in groups[WHITE-1]: print('      ', group)
  print()

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
  '''
  Extracts stone/liberty coordinate pairs and stores them as group
  '''
  group = {'stones': [], 'liberties' :[]}
  for row in range(width):
    for col in range(width):
      stone = marks[row][col]
      if stone == FENCE or stone == EMPTY: continue
      if stone == ESCAPE: group['liberties'].append((col, row))
      else: group['stones'].append((col, row))
  return group

def update_groups():
  global groups
  '''
  Keeps track of BLACK and WHITE groups on board by
  maintaining coordinates of stones and their liberties
  '''
  groups = [[], []]
  for row in range(width):
    for col in range(width):
      stone = board[row][col]
      if stone == FENCE or stone == EMPTY: continue
      marks = [[EMPTY for _ in range(width)] for _ in range(width)]
      if stone == BLACK:
        count(col, row, BLACK, marks)
        group = add_stones(marks, BLACK)
        if group not in groups[BLACK-1]: groups[BLACK-1].append(group)
      if stone == WHITE:
        count(col, row, WHITE, marks)
        group = add_stones(marks, WHITE)
        if group not in groups[WHITE-1]: groups[WHITE-1].append(group)

def is_clover(col, row):
  '''
  Returns color of clover shape surrounding current square
  or EMPTY if this is not a clover shape
  '''
  clover_color = -1
  other_color = -1
  for stone in [board[row][col+1], board[row][col-1], board[row+1][col], board[row-1][col]]:
    if stone == FENCE: continue
    if stone == EMPTY: return EMPTY
    if clover_color == -1:
      clover_color = stone
      other_color = (3-clover_color)
    elif stone == other_color: return EMPTY
  return clover_color

def play(col, row, color):
  global ko, side
  '''
  Sets stone of a given color at col, row,
  handles captures, sets new Ko square when needed.
  '''
  ko = [NONE, NONE]
  board[row][col] = color
  update_groups()
  for group in groups[(3-color-1)]:
    if len(group['liberties']) == 0:
      if len(group['stones']) == 1 and is_clover(col, row) == (3-side):
        ko = [group['stones'][0][0], group['stones'][0][1]]
      for stone in group['stones']:
        board[stone[1]][stone[0]] = EMPTY
  side = (3-color)

def genmove(color):
  '''
  Returns the best move to be played by the given color
  by considering the following heuristics:

  

  '''
  print(color)

def gtp():
  global width, side
  while True:
    command = input()
    if 'name' in command: print('= Gakusei\n')
    elif 'protocol_version' in command: print('= 1\n');
    elif 'version' in command: print('=', 'by Code Monkey King\n')
    elif 'list_commands' in command: print('= protocol_version\n')
    elif 'boardsize' in command: width = int(command.split()[1])+2; print('=\n')
    elif 'clear_board' in command: init_board(); print('=\n')
    elif 'showboard' in command: print('= Internal board:', end=''); print_board()
    elif 'play' in command:
      if 'pass' not in command:
        params = command.split()
        color = BLACK if params[1] == 'B' else WHITE
        col = ord(params[2][0])-ord('A')+(1 if ord(params[2][0]) <= ord('H') else 0)
        row = width-int(params[2][1:])-1
        play(col, row, color)
        print('=\n')
      else:
        side = (3-side)
        print('=\n')
    elif 'genmove' in command:
      best_move = genmove(BLACK if command.split()[-1] == 'B' else WHITE)
      print('=\n')
      #print('=', best_move, '\n')
    elif 'quit' in command: sys.exit()
    else: print('=\n') # skip currently unsupported commands

def debug():
  global width, board
  width=9+2
  init_board()
  board = [
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    [3, 0, 2, 0, 1, 0, 0, 0, 0, 0, 3],
    [3, 2, 0, 2, 1, 0, 1, 1, 1, 0, 3],
    [3, 0, 2, 1, 1, 0, 0, 0, 0, 0, 3],
    [3, 0, 0, 1, 2, 2, 0, 0, 1, 0, 3],
    [3, 0, 0, 1, 0, 2, 0, 2, 0, 0, 3],
    [3, 0, 0, 0, 0, 2, 2, 2, 0, 0, 3],
    [3, 0, 0, 0, 0, 2, 1, 2, 0, 0, 3],
    [3, 0, 0, 0, 0, 2, 1, 2, 0, 0, 3],
    [3, 0, 0, 0, 0, 0, 2, 0, 0, 0, 3],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
  ]
  print_board()
  print(is_clover(1,1))

def main():
  global width
  width=19+2;   # set board width + offboard squares
  init_board(); # set up board
  gtp()         # start GTP IO communication

#debug()
main()
