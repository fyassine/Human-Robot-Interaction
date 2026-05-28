#!/usr/bin/env python
"""This script is used to test UDP execution on the real Schunk robot.

Creator:
    Jakob Thumm
"""
from communi_cat.client_cat import ClientCat

import matplotlib.pyplot as plt
import numpy as np
import time


import threading

# Function to generate a sphere's surface points
def plot_sphere(ax, x_center, y_center, z_center, radius, color):
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    radius = 1
    
    # Parametric equation for a sphere
    x = radius * np.outer(np.cos(u), np.sin(v)) + x_center
    y = radius * np.outer(np.sin(u), np.sin(v)) + y_center
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v)) + z_center
    
    ax.plot_surface(x, y, z, color=color, rstride=5, cstride=5, alpha=0.6)

def data_receiver(client):
    while not stop_thread:
        client.receive_data()
    client.stop()

stop_thread = False
client = ClientCat()
client.start()
receiver_thread = threading.Thread(target=data_receiver, args=(client,))
receiver_thread.start()



if __name__ == "__main__":
    
    # Initialize plotting outside the loop
    plt.ion()  # Turn on interactive mode
    # Create the plot
    fig = plt.figure(figsize=(18, 8))
    ax1 = fig.add_subplot(111, projection='3d')

    colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown', 'pink', 'cyan', 'yellow']
    
    human_joint_names = ["lShoulder", "lElbow", "lHand", "rShoulder", "rElbow", "rHand", "Collar", "lElbow", "Head"]
    human_capsules = ["lUpperArm", "lLowerArm", "lHand", "rUpperArm", "rLowerArm", "rHand", "Torso", "Head"]
    
    # Display the plot window
    plt.show()

    
    sample_time = 0.01
    
    try:
        while True:

            data = client.data[-1]
            
            print(data[-36:])
            measured_points = np.array(data[-36:]).reshape(9, 4)
            measured_points = measured_points[:, :3]
            
                
            # Clear previous plot
            ax1.cla()
            
            # Set plot limits and labels
            ax1.set_xlim([-1, 1])
            ax1.set_ylim([-1, 1])
            ax1.set_zlim([-1, 1])
            ax1.set_title('Real-time Robot Data')
            
         
            # Plot measured_points
            for i in range(measured_points.shape[0]):
                x, y, z = measured_points[i]
                ax1.scatter(x, y, z, s=100, color=colors[i % len(colors)], label=human_joint_names[i])
                #plot_sphere(ax1, x, y, z, r, color=colors[i % len(colors)])

                
            ax1.legend()

            # Update the plot
            plt.draw()
            plt.pause(sample_time)
 
    except KeyboardInterrupt:
        pass
    finally:
        stop_thread = True


