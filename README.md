# Cutting Stock Problem
This respository contains the code for Cutting Stock Problem (1 Dimensional at the moment). The code for 2-D Cutting Stock Problem will be added soon. The code contains as much explanation as possible (also contains explanation from Serge Kruk's book).

## Quick Usage
You can use [CSP Tool](https://alternate.parts/csp) online
![CSP Tool](./github/CSP-Tool.PNG)

## Libraries
* [Google OR-Tools](https://developers.google.com/optimization)

## Setup
```bash
$ pip install ortools
```

## Run
If you run the `stock_cutter_1d.py` file directly, it runs the example which uses 120 as length of stock Rod and generates some customer rods to cut. You can update these at the end of `stock_cutter_1d.py`.
```bash
$ python stock_cutter_1d.py
```

Output:

```bash
numRollsUsed 5
Status: OPTIMAL
Roll #0: [0.0, [33, 33, 18, 18, 18]]
Roll #1: [2.9999999999999925, [33, 30, 18, 18, 18]]
Roll #2: [5.999999999999993, [30, 30, 18, 18, 18]]
Roll #3: [2.9999999999999987, [33, 33, 33, 18]]
Roll #4: [21.0, [33, 33, 33]]```
```

![Graph of Output](./github/graph-1d-b.PNG)

## Known Issues (help appreciated)
* Sometimes the results include extra number of customer items, even though they were not specfied in that amount. The [CSP Tool](https://alternate.parts/csp) alerts you about that so you could exclude those results. But if you can help us find the bug in the code, it would be great. 

## Resources
The whole code for this project is taken from Serge Kruk's
* [Practical Python AI Projects: Mathematical Models of Optimization Problems with Google OR-Tools](https://amzn.to/3iPceJD)
* [Repository of the code in Serge's book](https://github.com/sgkruk/Apress-AI/)
