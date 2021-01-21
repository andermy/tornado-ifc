import matplotlib.pyplot as plt
from shapely.geometry.polygon import LinearRing
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import nearest_points
import math
import numpy as np
from scipy.spatial import ConvexHull

def main(element):

    fig = plt.figure(1, figsize=(5,5), dpi=90)

    #pr = []
    #points = element.shape[0].shape2.get_verts()
    #for p in points:
    #    pr.append(p)
    #pocc_corners = np.array(pr)

    #pocc_corners = np.array(object.shape2.get_verts())
    #pocc_corners = pocc_corners*1000
    #ifc_corners = np.array(element.shape[0].get_points()) 
    #plot_object(ifc_corners, fig, '#FF5733')
    #plot_object(pocc_corners, fig, '#2edb48')

    plot_objects([element], fig, element.storey[0], None)
    plot_objects([element], fig, element.storey[0], "hgv")
    
    plt.axis('scaled')
    plt.show()

def main2(objects, floor):

    fig = plt.figure(1, figsize=(5,5), dpi=90)

    #plot_objects(objects, fig, floor, None)
    plot_objects(objects, fig, floor, "hgv")
    
    plt.axis('scaled')
    plt.show()

def plot_object(element, fig, color):
    try:
        polygon = Polygon(element[:,:2])
        x = []
        y = []
        for c in list(polygon.exterior.coords):
            x.append(c[0])
            y.append(c[1])
        x.append(polygon.exterior.coords[0][0])
        y.append(polygon.exterior.coords[0][0])
    except:
        print("no ifc corners")
        
    ax = fig.add_subplot(111)
    ax.plot(x, y, color=color, alpha=0.7,
        linewidth=3, solid_capstyle='round', zorder=2)
    ax.set_title('Polygon')

def plot_objects(elements, fig, floor, pyocc=None):
    for element in elements:
        if element.storey[0] == floor:
            if pyocc is None:
                try:
                    color = '#FF5733'
                    if element.shape[0].axis[0]>0:
                        color = '#512edb'
                    polygon = element.shape[0].get_points()
                    polygon = np.array(polygon)
                    polygon = polygon[:,:2]
                    x = []
                    y = []
                    for c in polygon:
                        x.append(c[0])
                        y.append(c[1])
                    x.append(polygon[0][0])
                    y.append(polygon[0][1])
                except:
                    print("No convex hull")
                    continue
            else:
                try:
                    color = '#2edb48'
                    if element.shape[0].need_section_for_footprint():
                        polygon = order_points(element.shape[0].footprint_sweptsolid())
                    else:
                        polygon = order_points(element.shape[0].get_vertices())
                    x = []
                    y = []
                    for c in polygon:
                        x.append(c[0]*1000)
                        y.append(c[1]*1000)
                    x.append(polygon[0][0]*1000)
                    y.append(polygon[0][1]*1000)
                except:
                    print("No convex hull")
                    continue
            
            ax = fig.add_subplot(111)
            ax.plot(x, y, color=color, alpha=0.7,
                linewidth=3, solid_capstyle='round', zorder=2)
            ax.set_title('Polygon')

def order_points(pts):
	# Creating the convex hull surrounding boundingbox
    pts = np.array(pts)
    pts = pts[:,:2]

    try:
        sortedC = pts[ConvexHull(pts[:,:2]).vertices]
        return sortedC
    except: 
        return np.array(pts)

