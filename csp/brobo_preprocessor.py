def buildBrobo(data, bladeKerf, savePath, programNum = 1):
    bladeKerf = inchToDecimalInch(bladeKerf)
    for stick in data:
        for i, element in enumerate(stick):
            stick[i] = inchToDecimalInch(element)
    


def inchToDecimalInch(measurement):
    return float(measurement) * 1000