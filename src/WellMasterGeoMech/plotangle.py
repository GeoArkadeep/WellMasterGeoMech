import matplotlib.pyplot as plt
import numpy as np

def plotfracs(data):
    x = data[:, 1]
    y = data[:, 0]
    angles = data[:, 2]

    # Creating the plot
    fig, ax = plt.subplots()
    ax.set_xlim(0, 180)  # Adjusting x-axis limit to fit your data
    #ax.set_ylim(2450, 2460)  # Adjusting y-axis limit to fit your data
    ax.set_aspect('equal', adjustable='box')  # This makes 1 unit in x equal to 1 unit in y

    # Plotting each line segment based on the angle
    for x_i, y_i, angle in zip(x, y, angles):
        # Calculating the end point of the line segment
        # Assuming a fixed length for each segment
        length = 1  # Adjusted length to be visible given the scale of your data
        end_x = x_i + length * np.cos(np.radians(angle))
        end_y = y_i + length * np.sin(np.radians(angle))
        
        # Plotting the line segment
        ax.plot([x_i, end_x], [y_i, end_y], linewidth=0.1, color='black')  # Added markers for clarity
    return plt
#plt.show()
