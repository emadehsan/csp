# Cutting Stock Problem
Cutting Stock Problem (CSP) deals with planning the cutting of items (rods / sheets) from given stock items (which are usually of fixed size).

## New to Cutting Stock Problem? Understand Visually
<a href="https://www.youtube.com/watch?v=4WXtfO9JB20" target="_blank">
	<img src="./github/video-thumb.jpg" alt="Video Tutorial on Cutting Stock Problem">
</a>


This implementation of CSP tries to answer
> How to minimize number of stock items used while cutting customer order


while doing so, it also caters
> How to cut the stock for customer orders so that waste is minimum


The OR Tools also helps us in calculating the number of possible solutions for your problem. So in addition, we can also compute
> In how many ways can we cut given order from fixed size Stock?


## Quick Usage
This is how CSP Tools looks in action. Click [CSP Tool](https://alternate.parts/csp) to use it
<a href="https://alternate.parts/csp">
	<img src="./github/CSP-Tool.PNG" alt="CSP Tool">
</a>

## Libraries
* [Google OR-Tools](https://developers.google.com/optimization)

## Quick Start
```bash
$ git clone https://github.com/emadehsan/csp
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
