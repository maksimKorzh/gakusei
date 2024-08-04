###############################################################################
#                                                                             #
#           GAKUSEI - An Old School Go/Weiqi/Baduk playing program            #
#                                                                             #
###############################################################################

import sys
import copy

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

def print_groups():
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

def make_group(col, row, color):
  '''
  Returns a group of a given color at col, row
  '''
  marks = [[EMPTY for _ in range(width)] for _ in range(width)]
  count(col, row, color, marks)
  return add_stones(marks, color)

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

      if stone == BLACK:
        group = make_group(col, row, BLACK)
        if group not in groups[BLACK-1]: groups[BLACK-1].append(group)
      if stone == WHITE:
        group = make_group(col, row, WHITE)
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

def is_suicide(col, row, color):
  '''
  Checks if the stone of a given color placed at col, row
  would result in group self capture, returns true if
  so and false otherwise
  '''
  suicide = False
  board[row][col] = color
  marks = [[EMPTY for _ in range(width)] for _ in range(width)]
  count(col, row, color, marks)
  group = add_stones(marks, color)
  if len(group['liberties']) == 0: suicide = True
  board[row][col] = EMPTY
  return suicide

def is_atari(col, row, color):
  '''
  Checks if the stone of a given color placed at col, row
  is in atari, returns true if so and false otherwise
  '''
  atari = False
  board[row][col] = color
  marks = [[EMPTY for _ in range(width)] for _ in range(width)]
  count(col, row, color, marks)
  group = add_stones(marks, color)
  if len(group['liberties']) == 1: atari = True
  board[row][col] = EMPTY
  return atari

def play(col, row, color):
  '''
  Sets stone of a given color at col, row,
  handles captures, sets new Ko square when needed.
  '''
  global ko, side
  ko = [NONE, NONE]
  board[row][col] = color
  update_groups()
  for group in groups[(3-color-1)]:
    if len(group['liberties']) == 0:
      if len(group['stones']) == 1 and is_clover(col, row) == (3-side):
        ko = group['stones'][0]
      for stone in group['stones']:
        board[stone[1]][stone[0]] = EMPTY
  side = (3-color)

def is_ladder(col, row, color):
  '''
  Resursively simulates a ladder chasing and
  figures out whether it works or not
  '''
  group = make_group(col, row, color)
  if len(group['liberties']) == 0:
    return True    
  if len(group['liberties']) == 1:
    board[row][col] = color
    new_col = group['liberties'][0][0]
    new_row = group['liberties'][0][1]
    if is_ladder(new_col, new_row, color): return 1
    board[row][col] = EMPTY
  if len(group['liberties']) == 2:
    for move in group['liberties']:
      board[move[1]][move[0]] = (3-color)
      group = make_group(col, row, color)
      new_col = group['liberties'][0][0]
      new_row = group['liberties'][0][1]
      if is_ladder(new_col, new_row, color): return move
      board[move[1]][move[0]] = EMPTY
  return 0


def check_ladder(col, row, color):
  '''
  Return true if ladder is working and false otherwise,
  initial group to check should contain 2 liberties
  '''
  global board
  current_board = copy.deepcopy(board)
  ladder = is_ladder(col, row, color)
  board = copy.deepcopy(current_board)
  return ladder


def attack(group, color):
  '''
  Returns the best move to attack a given group
  '''
  moves = []
  urgency = int(len(group['stones']) / len(group['liberties']))
  if len(group['liberties'])== 1: # capture group
    urgency *= (width*20)
    if group['liberties'][0] != ko:
      return [group['liberties'][0], urgency, 'capture']
  if len(group['liberties']) == 2: # check ladder attack
    stone = group['stones'][0]
    move = check_ladder(stone[0], stone[1], (3-color))
    if move:
      if not is_suicide(move[0], move[1], color):
        if not is_atari(move[0], move[1], color):
          urgency = (width*2)
          return [move, urgency, 'capture ladder']
  if len(group['liberties']) > 2: # surround group
    for move in group['liberties']:
      if not is_suicide(move[0], move[1], color):
        urgency = (abs(int(width/2) - move[0]) + abs(int(width/2) - move[1]))*5
        if (move[0] == 1 or move[1] == 1 or
            move[0] == (width-2) or move[1] == (width-2)):
            urgency = 3
        if is_atari(move[0], move[1], color): continue
        moves.append([move, urgency, 'surround'])
    if len(moves):
      moves.sort(key=lambda x: x[1])
      return moves[0]
  return NONE

def defend(group, color):
  '''
  Returns the best move to defend a given group
  '''
  moves = []
  urgency = int(len(group['stones']) / len(group['liberties']))
  if len(group['liberties'])== 1: # save group
    urgency *= (width*3)
    if (group['liberties'][0][0] == 1 or
        group['liberties'][0][1] == 1 or
        group['liberties'][0][0] == (width-2) or
        group['liberties'][0][1] == (width-2)):
        urgency = 2
    if not is_suicide(group['liberties'][0][0], group['liberties'][0][1], color):
      stone = group['stones'][0]
      ladder = check_ladder(stone[0], stone[1], color) # check if not trapped int a ladder
      if not ladder: return [group['liberties'][0], urgency, 'save']
  if len(group['liberties']) > 1: # extend group
    for move in group['liberties']:
      if not is_suicide(move[0], move[1], color):
        if not is_clover(move[0], move[1]):
          urgency = (abs(int(width/2) - move[0]) + abs(int(width/2) - move[1]))
          if (move[0] < 3 or move[1] < 3 or
              move[0] < (width-5) or move[1] < (width-5)):
              urgency = 1 # crawling on 1st and 2nd lines is bad
          moves.append([move, urgency, 'extend'])
    if len(moves):
      moves.sort(key=lambda x: x[1], reverse=True)
      return moves[0]
  return NONE

def genmove(color):
  '''
  Returns the best move to be played by the given
  color, considering the following heuristics:

  1. ATTACK OPPONENT'S GROUP
  2. DEFEND OWN GROUP
  3. MATCH PATTERNS

  There might be several attacking moves, several
  defensive ones and a few pattern matches. Each
  move gets assigned the value of its "urgency".
  For a contact play (attack/defense) "urgency" is
  calculated via dividing the number of stones by
  the amount of liberties, the higher value we have
  the more urgent a given move is.

  For pattern matching
  "urgency" is assigned with...

  Eventually
  a move with the biggest urgency is considered to be
  the best.
  '''
  
  # First we need to get all attacking moves,
  # so we loop over opponent's group and call
  # attack(group) to return the best attacking
  # move with associated urgency.
  update_groups()
  moves = []
  for group in groups[(3-color-1)]: # attack opponent's weakest group
    move = attack(group, color)
    if move != NONE and move not in moves:
      moves.append(move)
  
  for group in groups[(color-1)]: # defend own weakest group
    move = defend(group, color)
    if move != NONE and move not in moves:
      moves.append(move)
  
  # Sort moves in place by urgency in descending order
  if len(moves):
    moves.sort(key=lambda x: x[1], reverse=True)
    # debug print generated moves stats
    for move in moves: print(move_to_string(move[0]), move[1], move[2], file=sys.stderr)
    if moves[0][1] > 1: return moves[0][0]
  return NONE

def move_to_string(move):
  '''
  Converts move (col, row) to algebraic notation
  '''
  global width
  col = chr(move[0]-(1 if move[0]<=8 else 0)+ord('A'))
  row = str(width-move[1]-1)
  return col+row

def gtp():
  '''
  Handles GTP communication between engine and GUI
  '''
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
      color = BLACK if command.split()[-1] == 'B' else WHITE
      best_move = genmove(color)
      if best_move != NONE:
        play(best_move[0], best_move[1], color)
        print('= ' + move_to_string(best_move) + '\n')
      else: print('= pass\n')
    elif 'quit' in command: sys.exit()
    else: print('=\n') # skip currently unsupported commands

def debug():
  global width, board
  width=9+2
  init_board()
  #board = [
  #  [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
  #  [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
  #  [3, 0, 0, 1, 1, 1, 0, 0, 0, 0, 3],
  #  [3, 0, 1, 2, 2, 0, 0, 0, 0, 0, 3],
  #  [3, 0, 0, 1, 0, 1, 0, 0, 0, 0, 3],
  #  [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
  #  [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
  #  [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
  #  [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
  #  [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
  #  [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
  #]
  board = [
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [3, 0, 0, 1, 1, 1, 0, 0, 0, 0, 3],
    [3, 0, 1, 2, 2, 1, 0, 0, 0, 0, 3],
    [3, 0, 0, 1, 2, 0, 0, 0, 0, 0, 3],
    [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
  ]

  print('ladder', check_ladder(4, 3, WHITE))
  print_board()
  update_groups()
  print_groups()

  gtp()

def main():
  global width
  width=19+2;   # set board width + offboard squares
  init_board(); # set up board
  gtp()         # start GTP IO communication

#debug()
main()
