'''
Original Author: Serge Kruk
Original Version: https://github.com/sgkruk/Apress-AI/blob/master/cutting_stock.py

Updated by: Emad Ehsan
'''
from ortools.linear_solver import pywraplp
from math import ceil
from random import randint
import json
from read_lengths import get_data
import typer
from typing import Optional

def newSolver(name,integer=False):
  return pywraplp.Solver(name,\
                         pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING \
                         if integer else \
                         pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)

'''
return a printable value
'''
def SolVal(x):
  if type(x) is not list:
    return 0 if x is None \
      else x if isinstance(x,(int,float)) \
           else x.SolutionValue() if x.Integer() is False \
                else int(x.SolutionValue())
  elif type(x) is list:
    return [SolVal(e) for e in x]

def ObjVal(x):
  return x.Objective().Value()


def gen_data(num_orders):
    R=[] # small rolls
    # S=0 # seed?
    for i in range(num_orders):
        R.append([randint(1,12), randint(5,40)])
    return R


def solve_model(demands, parent_width=100):
  '''
      demands = [
          [1, 3], # [quantity, width]
          [3, 5],
          ...
      ]

      parent_width = integer
  '''
  num_orders = len(demands)
  solver = newSolver('Cutting Stock', True)
  k,b  = bounds(demands, parent_width)

  # array of boolean declared as int, if y[i] is 1, 
  # then y[i] Big roll is used, else it was not used
  y = [ solver.IntVar(0, 1, f'y_{i}') for i in range(k[1]) ] 

  # x[i][j] = 3 means that small-roll width specified by i-th order
  # must be cut from j-th order, 3 tmies 
  x = [[solver.IntVar(0, b[i], f'x_{i}_{j}') for j in range(k[1])] \
      for i in range(num_orders)]
  
  unused_widths = [ solver.NumVar(0, parent_width, f'w_{j}') \
      for j in range(k[1]) ] 
  
  # will contain the number of big rolls used
  nb = solver.IntVar(k[0], k[1], 'nb')

  # consntraint: demand fullfilment
  for i in range(num_orders):  
    # small rolls from i-th order must be at least as many in quantity
    # as specified by the i-th order
    solver.Add(sum(x[i][j] for j in range(k[1])) >= demands[i][0]) 

  # constraint: max size limit
  for j in range(k[1]):
    # total width of small rolls cut from j-th big roll, 
    # must not exceed big rolls width
    solver.Add( \
        sum(demands[i][1]*x[i][j] for i in range(num_orders)) \
        <= parent_width*y[j] \
      ) 

    # width of j-th big roll - total width of all orders cut from j-th roll
    # must be equal to unused_widths[j]
    # So, we are saying that assign unused_widths[j] the remaining width of j'th big roll
    solver.Add(parent_width*y[j] - sum(demands[i][1]*x[i][j] for i in range(num_orders)) == unused_widths[j])

    '''
    Book Author's note from page 201:
    [the following constraint]  breaks the symmetry of multiple solutions that are equivalent 
    for our purposes: any permutation of the rolls. These permutations, and there are K! of 
    them, cause most solvers to spend an exorbitant time solving. With this constraint, we 
    tell the solver to prefer those permutations with more cuts in roll j than in roll j + 1. 
    The reader is encouraged to solve a medium-sized problem with and without this 
    symmetry-breaking constraint. I have seen problems take 48 hours to solve without the 
    constraint and 48 minutes with. Of course, for problems that are solved in seconds, the 
    constraint will not help; it may even hinder. But who cares if a cutting stock instance 
    solves in two or in three seconds? We care much more about the difference between two 
    minutes and three hours, which is what this constraint is meant to address
    '''
    if j < k[1]-1: # k1 = total big rolls
      # total small rolls of i-th order cut from j-th big roll must be >=
      # totall small rolls of i-th order cut from j+1-th big roll
      solver.Add(sum(x[i][j] for i in range(num_orders)) >= sum(x[i][j+1] for i in range(num_orders)))

  # find & assign to nb, the number of big rolls used
  solver.Add(nb == solver.Sum(y[j] for j in range(k[1])))

  ''' 
    minimize total big rolls used
    let's say we have y = [1, 0, 1]
    here, total big rolls used are 2. 0-th and 2nd. 1st one is not used. So we want our model to use the 
    earlier rolls first. i.e. y = [1, 1, 0]. 
    The trick to do this is to define the cost of using each next roll to be higher. So the model would be
    forced to used the initial rolls, when available, instead of the next rolls.

    So instead of Minimize ( Sum of y ) or Minimize( Sum([1,1,0]) )
    we Minimize( Sum([1*1, 1*2, 1*3]) )
  ''' 

  '''
  Book Author's note from page 201:

  There are alternative objective functions. For example, we could have minimized the sum of the waste. This makes sense, especially if the demand constraint is formulated as an inequality. Then minimizing the sum of waste Chapter 7  advanCed teChniques
  will spend more CPU cycles trying to find more efficient patterns that over-satisfy demand. This is especially good if the demand widths recur regularly and storing cut rolls in inventory to satisfy future demand is possible. Note that the running time will grow quickly with such an objective function
  '''

  Cost = solver.Sum((j+1)*y[j] for j in range(k[1]))

  solver.Minimize(Cost)

  status = solver.Solve()
  numRollsUsed = SolVal(nb)

  return status, \
    numRollsUsed, \
    rolls(numRollsUsed, SolVal(x), SolVal(unused_widths), demands), \
    SolVal(unused_widths), \
    solver.WallTime()

def bounds(demands, parent_width=100):
  '''
  b = [sum of widths of individual small rolls of each order]
  T = local var. stores sum of widths of adjecent small-rolls. When the width reaches 100%, T is set to 0 again.
  k = [k0, k1], k0 = minimum big-rolls requierd, k1: number of big rolls that can be consumed / cut from
  TT = local var. stores sum of widths of of all small-rolls. At the end, will be used to estimate lower bound of big-rolls
  '''
  num_orders = len(demands)
  b = []
  T = 0
  k = [0,1]
  TT = 0

  for i in range(num_orders):
    # q = quantity, w = width; of i-th order
    quantity, width = demands[i][0], demands[i][1]
    # TODO Verify: why min of quantity, parent_width/width?
    # assumes widths to be entered as percentage
    # int(round(parent_width/demands[i][1])) will always be >= 1, because widths of small rolls can't exceed parent_width (which is width of big roll)
    # b.append( min(demands[i][0], int(round(parent_width / demands[i][1]))) )
    b.append( min(quantity, int(round(parent_width / width))) )

    # if total width of this i-th order + previous order's leftover (T) is less than parent_width
    # it's fine. Cut it.
    if T + quantity*width <= parent_width:
      T, TT = T + quantity*width, TT + quantity*width
    # else, the width exceeds, so we have to cut only as much as we can cut from parent_width width of the big roll
    else:
      while quantity:
        if T + width <= parent_width:
          T, TT, quantity = T + width, TT + width, quantity-1
        else:
          k[1],T = k[1]+1, 0 # use next roll (k[1] += 1)
  k[0] = int(round(TT/parent_width+0.5))

  print('k', k)
  print('b', b)

  return k, b

'''
  nb: array of number of rolls to cut, of each order
  
  w: 
  demands: [
    [quantity, width],
    [quantity, width],
    [quantity, width],
  ]
'''
def rolls(nb, x, w, demands):
  consumed_big_rolls = []
  num_orders = len(x) 
  # go over first row (1st order)
  # this row contains the list of all the big rolls available, and if this 1st (0-th) order
  # is cut from any big roll, that big roll's index would contain a number > 0
  for j in range(len(x[0])):
    # w[j]: width of j-th big roll 
    # int(x[i][j]) * [demands[i][1]] width of all i-th order's small rolls that are to be cut from j-th big roll 
    RR = [ abs(w[j])] + [ int(x[i][j])*[demands[i][1]] for i in range(num_orders) \
                    if x[i][j] > 0 ] # if i-th order has some cuts from j-th order, x[i][j] would be > 0
    consumed_big_rolls.append(RR)

  return consumed_big_rolls



'''
this model starts with some patterns and then optimizes those patterns
'''
def solve_large_model(demands, parent_width=100):
  num_orders = len(demands)
  iter = 0
  patterns = get_initial_patterns(demands)
  # print('method#solve_large_model, patterns', patterns)

  # list quantities of orders
  quantities = [demands[i][0] for i in range(num_orders)]
  print('quantities', quantities)

  while iter < 20:
    status, y, l = solve_master(patterns, quantities, parent_width=parent_width)
    iter += 1

    # list widths of orders
    widths = [demands[i][1] for i in range(num_orders)]
    new_pattern, objectiveValue = get_new_pattern(l, widths, parent_width=parent_width)

    # print('method#solve_large_model, new_pattern', new_pattern)
    # print('method#solve_large_model, objectiveValue', objectiveValue)

    for i in range(num_orders):
      # add i-th cut of new pattern to i-thp pattern
      patterns[i].append(new_pattern[i])

  status, y, l = solve_master(patterns, quantities, parent_width=parent_width, integer=True)  

  return status, \
          patterns, \
          y, \
          rolls_patterns(patterns, y, demands, parent_width=parent_width)


'''
Dantzig-Wolfe decomposition splits the problem into a Master Problem MP and a sub-problem SP.

The Master Problem: provided a set of patterns, find the best combination satisfying the demand

C: patterns
b: demand
'''
def solve_master(patterns, quantities, parent_width=100, integer=False):
  title = 'Cutting stock master problem'
  num_patterns = len(patterns)
  n = len(patterns[0])
  # print('**num_patterns x n: ', num_patterns, 'x', n)
  # print('**patterns recived:')
  # for p in patterns:
  #   print(p)

  constraints = []

  solver = newSolver(title, integer)

  # y is not boolean, it's an integer now (as compared to y in approach used by solve_model)
  y = [ solver.IntVar(0, 1000, '') for j in range(n) ] # right bound?
  # minimize total big rolls (y) used
  Cost = sum(y[j] for j in range(n)) 
  solver.Minimize(Cost)

  # for every pattern
  for i in range(num_patterns):
    # add constraint that this pattern (demand) must be met
    # there are m such constraints, for each pattern
    constraints.append(solver.Add( sum(patterns[i][j]*y[j] for j in range(n)) >= quantities[i]) ) 

  status = solver.Solve()
  y = [int(ceil(e.SolutionValue())) for e in y]

  l =  [0 if integer else constraints[i].DualValue() for i in range(num_patterns)]
  # sl =  [0 if integer else constraints[i].name() for i in range(num_patterns)]
  # print('sl: ', sl)

  # l =  [0 if integer else u[i].Ub() for i in range(m)]
  toreturn = status, y, l
  # l_to_print = [round(dd, 2) for dd in toreturn[2]]
  # print('l: ', len(l_to_print), '->', l_to_print)
  # print('l: ', toreturn[2])
  return toreturn

def get_new_pattern(l, w, parent_width=100):
  solver = newSolver('Cutting stock sub-problem', True)
  n = len(l)
  new_pattern = [ solver.IntVar(0, parent_width, '') for i in range(n) ]

  # maximizes the sum of the values times the number of occurrence of that roll in a pattern
  Cost = sum( l[i] * new_pattern[i] for i in range(n))
  solver.Maximize(Cost)

  # ensuring that the pattern stays within the total width of the large roll 
  solver.Add( sum( w[i] * new_pattern[i] for i in range(n)) <= parent_width ) 

  status = solver.Solve()
  return SolVal(new_pattern), ObjVal(solver)


'''
the initial patterns must be such that they will allow a feasible solution, 
one that satisfies all demands. 
Considering the already complex model, let’s keep it simple. 
Our initial patterns have exactly one roll per pattern, as obviously feasible as inefficient.
'''
def get_initial_patterns(demands):
  num_orders = len(demands)
  return [[0 if j != i else 1 for j in range(num_orders)]\
          for i in range(num_orders)]

def rolls_patterns(patterns, y, demands, parent_width=100):
  R, m, n = [], len(patterns), len(y)

  for j in range(n):
    for _ in range(y[j]):
      RR = []
      for i in range(m):
        if patterns[i][j] > 0:
          RR.extend( [demands[i][1]] * int(patterns[i][j]) )
      used_width = sum(RR)
      R.append([parent_width - used_width, RR])

  return R


'''
checks if all small roll widths (demands) smaller than parent roll's width
'''
def checkWidths(demands, parent_width):
  for quantity, width in demands:
    if width > parent_width:
      print(f'Small roll width {width} is greater than parent rolls width {parent_width}. Exiting')
      return False
  return True


'''
    params
        child_rolls: 
            list of lists, each containing quantity & width of rod / roll to be cut
            e.g.: [ [quantity, width], [quantity, width], ...]
        parent_rolls: 
            list of lists, each containing quantity & width of rod / roll to cut from
            e.g.: [ [quantity, width], [quantity, width], ...]
'''
def StockCutter1D(child_rolls, parent_rolls, output_json=True, large_model=True):

  # at the moment, only parent one width of parent rolls is supported
  # quantity of parent rolls is calculated by algorithm, so user supplied quantity doesn't matter?
  # TODO: or we can check and tell the user the user when parent roll quantity is insufficient
  parent_width = parent_rolls[0][1]

  if not checkWidths(demands=child_rolls, parent_width=parent_width):
    return []


  print('child_rolls', child_rolls)
  print('parent_rolls', parent_rolls)

  if not large_model:
    print('Running Small Model...')
    status, numRollsUsed, consumed_big_rolls, unused_roll_widths, wall_time = \
              solve_model(demands=child_rolls, parent_width=parent_width)

    # convert the format of output of solve_model to be exactly same as solve_large_model
    print('consumed_big_rolls before adjustment: ', consumed_big_rolls)
    new_consumed_big_rolls = []
    for big_roll in consumed_big_rolls:
      if len(big_roll) < 2:
        # sometimes the solve_model return a solution that contanis an extra [0.0] entry for big roll
        consumed_big_rolls.remove(big_roll)
        continue
      unused_width = big_roll[0]
      subrolls = []
      for subitem in big_roll[1:]:
        if isinstance(subitem, list):
          # if it's a list, concatenate with the other lists, to make a single list for this big_roll
          subrolls = subrolls + subitem
        else:
          # if it's an integer, add it to the list
          subrolls.append(subitem)
      new_consumed_big_rolls.append([unused_width, subrolls])
    print('consumed_big_rolls after adjustment: ', new_consumed_big_rolls)
    consumed_big_rolls = new_consumed_big_rolls
  
  else:
    print('Running Large Model...');
    status, A, y, consumed_big_rolls = solve_large_model(demands=child_rolls, parent_width=parent_width)

  numRollsUsed = len(consumed_big_rolls)
  # print('A:', A, '\n')
  # print('y:', y, '\n')


  STATUS_NAME = ['OPTIMAL',
    'FEASIBLE',
    'INFEASIBLE',
    'UNBOUNDED',
    'ABNORMAL',
    'NOT_SOLVED'
    ]

  output = {
      "statusName": STATUS_NAME[status],
      "numSolutions": '1',
      "numUniqueSolutions": '1',
      "numRollsUsed": numRollsUsed,
      "solutions": consumed_big_rolls # unique solutions
  }


  # print('Wall Time:', wall_time)
  print('numRollsUsed', numRollsUsed)
  print('Status:', output['statusName'])
  print('Solutions found :', output['numSolutions'])
  print('Unique solutions: ', output['numUniqueSolutions'])

  if output_json:
    return json.dumps(output)        
  else:
    return consumed_big_rolls


'''
Draws the big rolls on the graph. Each horizontal colored line represents one big roll.
In each big roll (multi-colored horizontal line), each color represents small roll to be cut from it.
If the big roll ends with a black color, that part of the big roll is unused width.

TODO: Assign each child roll a unique color
'''
def drawGraph(consumed_big_rolls, child_rolls, parent_width):
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    # TODO: to add support for multiple different parent rolls, update here
    xSize = parent_width # width of big roll
    ySize = 10 * len(consumed_big_rolls) # one big roll will take 10 units vertical space

    # draw rectangle
    fig,ax = plt.subplots(1)
    plt.xlim(0, xSize)
    plt.ylim(0, ySize)
    plt.gca().set_aspect('equal', adjustable='box')
    
    # print coords
    coords = []
    colors = ['r', 'g', 'b', 'y', 'brown', 'violet', 'pink', 'gray', 'orange', 'b', 'y']
    colorDict = {}
    i = 0
    for quantity, width in child_rolls:
      colorDict[width] = colors[i % 11]
      i+= 1

    # start plotting each big roll horizontly, from the bottom
    y1 = 0
    for i, big_roll in enumerate(consumed_big_rolls):
      '''
        big_roll = [leftover_width, [small_roll_1_1, small_roll_1_2, other_small_roll_2_1]]
      '''
      unused_width = big_roll[0]
      small_rolls = big_roll[1]

      x1 = 0
      x2 = 0
      y2 = y1 + 8 # the height of each big roll will be 8 
      for j, small_roll in enumerate(small_rolls):
        x2 = x2 + small_roll
        print(f"{x1}, {y1} -> {x2}, {y2}")
        width = abs(x1-x2)
        height = abs(y1-y2)
        # print(f"Rect#{idx}: {width}x{height}")
        # Create a Rectangle patch
        rect_shape = patches.Rectangle((x1,y1), width, height, facecolor=colorDict[small_roll], label=f'{small_roll}')
        ax.add_patch(rect_shape) # Add the patch to the Axes
        x1 = x2 # x1 for next small roll in same big roll will be x2 of current roll 

      # now that all small rolls have been plotted, check if a there is unused width in this big roll
      # set the unused width at the end as black colored rectangle
      if unused_width > 0:
        width = unused_width
        rect_shape = patches.Rectangle((x1,y1), width, height, facecolor='black', label='Unused')
        ax.add_patch(rect_shape) # Add the patch to the Axes

      y1 += 10 # next big roll will be plotted on top of current, a roll height is 8, so 2 will be margin between rolls

    plt.show()


if __name__ == '__main__':

  # child_rolls = [
  #    [quantity, width],
  # ]
  app = typer.Typer()


  def main(infile_name: Optional[str] = typer.Argument(None)):

    if infile_name:
      child_rolls = get_data(infile_name)
    else:
      child_rolls = gen_data(3)
    parent_rolls = [[10, 120]] # 10 doesn't matter, itls not used at the moment

    consumed_big_rolls = StockCutter1D(child_rolls, parent_rolls, output_json=False, large_model=False)
    typer.echo(f"{consumed_big_rolls}")


    for idx, roll in enumerate(consumed_big_rolls):
      typer.echo(f"Roll #{idx}:{roll}")

    drawGraph(consumed_big_rolls, child_rolls, parent_width=parent_rolls[0][1])

if __name__ == "__main__":
  typer.run(main)
