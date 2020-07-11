import numpy as np
from shapely.geometry import Polygon, Point
from scipy.spatial import ConvexHull
from shapely.ops import nearest_points


def shape(element):
    corners = element.vertices.all()
    corners2 = []
    
    for i in range(len(corners)):
        corners2.append([corners[i].get_X(), corners[i].get_Y(), corners[i].get_Z()])
    
    numpyC = np.array(corners2)

    sortedC = numpyC[ConvexHull(numpyC[:,:2]).vertices][:,:2]
    polygon = Polygon(sortedC)
    return polygon

def distance2D(P1, P2):
    import math
    return math.sqrt(math.pow(P1.get_X() - P2.get_X(), 2) +
                         math.pow(P1.get_Y() - P2.get_Y(), 2))    