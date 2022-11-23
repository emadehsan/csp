from __future__ import print_function
import collections, json
from ortools.sat.python import cp_model

# to draw rectangles
import matplotlib.pyplot as plt
import matplotlib.patches as patches

"""
    Cutting Stock problem
    params
        child_rects: 
            lists of multiple rectangles' coords
            e.g.: [ [w, h], [w, h], ...]
        parent_rects: rectangle coords
            lists of multiple rectangles' coords
            e.g.: [ [w, h], [w, h], ...]
"""
def StockCutter(child_rects, parent_rects):
    
    # Create the model
    model = cp_model.CpModel()

    # parent rect (to cut from). horizon = [ width, height ] of parent sheet
    # for now, parent rectangle is just one
    # TODO: to add functionality of cutting from multiple parent sheets, start here:
    horizon = parent_rects[0] 

    # Named Tuple to store information about created variables
    sheet_type = collections.namedtuple('sheet_type', 'x1 y1 x2 y2 x_interval y_interval')

    # Store for all model variables
    all_vars = {}

    # sum of to save area of all small rects, to cut from parent rect
    total_child_area = 0 

    # hold the widths (x) and heights (y) interval vars of each sheet
    x_intervals = []
    y_intervals = []

    # create model vars and intervals
    for rect_id, rect in enumerate(child_rects):
        width = rect[0]
        height = rect[1]
        area = width * height
        total_child_area += area
        # print(f"Rect: {width}x{height}, Area: {area}")

        suffix = '_%i_%i' % (width, height)

        # interval to represent width. max value can be the width of parent rect
        x1_var = model.NewIntVar(0, horizon[0], 'x1' + suffix)
        x2_var = model.NewIntVar(0, horizon[0], 'x2' + suffix)
        x_interval_var = model.NewIntervalVar(x1_var, width, x2_var, 'x_interval' + suffix)

        # interval to represent height. max value can be the height of parent rect
        y1_var = model.NewIntVar(0, horizon[1], 'y1' + suffix)
        y2_var = model.NewIntVar(0, horizon[1], 'y2' + suffix)
        y_interval_var = model.NewIntervalVar(y1_var, height, y2_var, 'y_interval' + suffix)
        
        x_intervals.append(x_interval_var)
        y_intervals.append(y_interval_var)

        # store the variables for later use
        all_vars[rect_id] = sheet_type(
            x1=x1_var, 
            y1=y1_var, 
            x2=x2_var, 
            y2=y2_var, 
            x_interval=x_interval_var,
            y_interval=y_interval_var
        )

    # add constraint: no over lap of rectangles allowed
    model.AddNoOverlap2D(x_intervals, y_intervals)

    # Solve model
    solver = cp_model.CpSolver()

    solution_printer = VarArraySolutionPrinter(all_vars)

    # Search for all solutions is only defined on satisfiability problems
    status = solver.SearchForAllSolutions(model, solution_printer) # use for satisfiability problem
    # status = solver.Solve(model) # use for Optimization Problem

    print('Status:', solver.StatusName(status))
    print('Solutions found :', solution_printer.solution_count())

    solutions = solution_printer.get_unique_solutions()    

    # call draw methods here, if want to draw with matplotlib

    int_solutions = solutions_to_int(solutions)

    statusName = solver.StatusName(status)
    numSolutions = solution_printer.solution_count()
    numUniqueSolutions = len(solutions)

    output = {
        "statusName": statusName,
        "numSolutions": numSolutions,
        "numUniqueSolutions": numUniqueSolutions,
        "solutions": int_solutions # unique solutions
    }

    # return json.dumps(output)

    # draw
    for idx, sol in enumerate(solutions):
        # sol is string of coordinates of all rectangles in this solution
        # format: x1,y1,x2,y2-x1,y1,x2,y2
        print('Sol#', idx)
        rect_strs = sol.split('-')
        rect_coords = [
            #    [x1,y1,x2,y2],
            #    [x1,y1,x2,y2],
        ]
        for rect_str in rect_strs:
            coords_str = rect_str.split(',')
            coords = [int(c) for c in coords_str]
            rect_coords.append(coords)
        print('rect_coords')
        # print(rect_coords)
        drawRectsFromCoords(rect_coords)

def drawRectsFromCoords(rect_coords):
    # draw rectangle
    fig,ax = plt.subplots(1)
    plt.xlim(0,6) # todo 7
    plt.ylim(0,6)
    plt.gca().set_aspect('equal', adjustable='box')
    
    # print coords
    coords = []
    colors = ['r', 'g', 'b', 'y', 'brown', 'black', 'violet', 'pink', 'gray', 'orange', 'b', 'y']
    for idx, coords in enumerate(rect_coords):
        x1=coords[0]
        y1=coords[1]
        x2=coords[2]
        y2=coords[3]
        # print(f"{x1}, {y1} -> {x2}, {y2}")

        width = abs(x1-x2)
        height = abs(y1-y2)
        # print(f"Rect#{idx}: {width}x{height}")

        # Create a Rectangle patch
        rect_shape = patches.Rectangle((x1,y1), width, height,facecolor=colors[idx])
        # Add the patch to the Axes
        ax.add_patch(rect_shape)
    plt.show()





"""
    TODO complete this, add to git
    params:
        str_solutions: list of strings. 1 string contains is solution
"""
def solutions_to_int(str_solutions):

    # list of solutions, each solution is a list of rectangle coords that look like [x1,y1,x2,y2]
    int_solutions = []

    # go over all solutions and convert them to int>list>json
    for idx, sol in enumerate(str_solutions):
        # sol is string of coordinates of all rectangles in this solution
        # format: x1,y1,x2,y2-x1,y1,x2,y2
    
        rect_strs = sol.split('-')
        rect_coords = [
            # [x1,y1,x2,y2],
            # [x1,y1,x2,y2],
            # ...
        ]

        # convert each rectangle's coords to int
        for rect_str in rect_strs:
            coords_str = rect_str.split(',')
            coords = [int(c) for c in coords_str]
            rect_coords.append(coords)

        # print('rect_coords', rect_coords)

        # call draw methods here, if want to draw individual solutions with matplotlib

        int_solutions.append(rect_coords)

    return int_solutions


"""
    To get all the solutions of the problem, as they come up. 
    https://developers.google.com/optimization/cp/cp_solver#all_solutions

    The solutions are all unique. But for the child rectangles that have same dimensions, 
    some solution will be repetitive. Because for the algorithm, they are different solutions, 
    but because of same size, they are merely permutations of the similar child rectangles - 
    having other rectangles' positions fixed.

    We want to remove repetitive extra solutions. One way to do this is
        1. Stringify every rectangle coords in a solution
            (1,2)->(2,3) becomes "1,2,2,3"

            # here the rectangles are stored as a string: "1,2,2,3" where x1=1, y1=2, x2=2, y2=3
        
        2. Put all these string coords into a sorted list. This sorting is important. 
            Because the rectangles (1,2)->(2,3) and (3,3)->(4,4) are actually same size (1x1) rectangles. 
            And they can appear in 1st solution as 
            [(1,2)->(2,3)   ,   (3,3)->(4,4)]
            and in the 2nd solution as
            [(3,3)->(4,4)   ,   (1,2)->(2,3)]

            but this sorted list of strings will ensure both solutions are represented as

            [..., "1,2,2,3", "3,3,4,4", ...]

        3. Join the Set of "strings (rectangles)" in to one big string seperated by '-'. For every solution.
            So in resulting big strings (solutions), we will have two similar strings (solutions) 
            that be similar and also contain

            "....1,2,2,3-3,3,4,4-...."

        4. Now add all these "strings (solutions)" into a Set. this adding to the set 
        will remove similar strings. And hence duplicate solutions will be removed.

"""
class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):

    def __init__(self, variables):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables
        self.__solution_count = 0

        # hold the calculated solutions
        self.__solutions = []
        self.__unique_solutions = set()

    def on_solution_callback(self):
        self.__solution_count += 1
        # print('Sol#: ', self.__solution_count)

        # using list to hold the coordinate strings of rectangles
        rect_strs = []

        # extra coordinates of all rectangles for this solution 
        for rect_id in self.__variables:
            rect = self.__variables[rect_id]
            x1 = self.Value(rect.x1)
            x2 = self.Value(rect.x2)
            y1 = self.Value(rect.y1)
            y2 = self.Value(rect.y2)

            rect_str = f"{x1},{y1},{x2},{y2}"
            # print(rect_str)

            rect_strs.append(rect_str)
            # print(f'Rect #{rect_id}: {x1},{y1} -> {x2},{y2}')

        # print(rect_strs)

        # sort the rectangles
        rect_strs = sorted(rect_strs)

        # single solution as a string
        solution_str = '-'.join(rect_strs)
        # print(solution_str)

        # store the solutions
        self.__solutions.append(solution_str)
        self.__unique_solutions.add(solution_str) # __unique_solutions is a set, so duplicates will get removed


    def solution_count(self):
        return self.__solution_count

    # returns all solutions  
    def get_solutions(self):
        return self.__solutions

    """
    returns unique solutions
    returns the permutation free list of solution strings  
    """
    def get_unique_solutions(self):
        return list(self.__unique_solutions) # __unique_solutions is a Set, convert to list



# for testing
if __name__ == '__main__':

    child_rects = [
        # [2, 2],
        # [1, 3],
        # [4, 3],
        # [1, 1],
        # [2, 4],

        [3, 3],
        [3, 3],
        [3, 3],
        [3, 3],
    ]

    parent_rects = [[6,6]]

    StockCutter(child_rects, parent_rects)