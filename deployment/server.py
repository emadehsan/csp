from flask import Flask, json, request
from flask_cors import CORS, cross_origin

import stock_cutter # local module

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/', methods=['GET'])
@cross_origin()
def get_csp():
	return 'Cutting Stock Problem'

'''
route for receving data for 1D problem 
'''
@app.route('/stocks_1d', methods=['POST'])
@cross_origin()
def post_stocks_1d():
	'''
	expects two params to be present
	child_rolls:
		array of arrays. E.g [ [quantity, width], [quantity, width], ... ]

	parent_rolls:
		array of arrays. E.g [ [quantity, width], [quantity, width], ... ]
	'''
	import stock_cutter_1d

	data = request.json
	print('data: ', data)

	child_rolls = data['child_rolls']
	parent_rolls = data['parent_rolls']

	'''
	it can be
	exactCuts: cut exactly as many as specified by user
	minWaste: cut some items, more than specified, to avoid waste
	'''
	cutStyle = data['cutStyle']

	# output = stock_cutter_1d.StockCutter1D(child_rolls, parent_rolls, cutStyle=cutStyle)
	output = stock_cutter_1d.StockCutter1D(child_rolls, parent_rolls, large_model=False, cutStyle=cutStyle)

	return output



'''
route for 2D
'''
@app.route('/stocks_2d', methods=['POST'])
@cross_origin()
def post_stocks():
	'''
	expects two params to be present
	child_rects:
		array of arrays. Each inner array is like [w, h] i.e. width & height of rectangle

	parent_rects:
		array of arrays. Each inner array is like [w, h] i.e. width & height of rectangle
	'''
	data = request.json
	print('data: ', data)

	child_rects = data['child_rects']
	parent_rects = data['parent_rects']

	output = stock_cutter.StockCutter(child_rects, parent_rects)

	return output



if __name__ == '__main__':
    # app.run()
	app.run(threaded=True, port=5000)
