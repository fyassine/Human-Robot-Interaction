#!/usr/bin/env python
"""This script is used to test UDP execution on the real Schunk robot.

Creator:
    Jakob Thumm
"""
from communi_cat.client_cat import ClientCat

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import time


import threading

# Function to generate a sphere's surface points
def plot_sphere(ax, x_center, y_center, z_center, radius, color):
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    
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
    ax1 = fig.add_subplot(131, projection='3d')
    ax2 = fig.add_subplot(132, projection='3d')
    ax3 = fig.add_subplot(133, projection='3d')
    colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown', 'pink', 'cyan', 'yellow', 'black', 'gray']
    
    human_joint_names = ["lShoulder", "lElbow", "lHand", "rShoulder", "rElbow", "rHand", "Collar", "Torso", "Head"]
    human_capsules = ["lUpperArm", "lLowerArm", "lHand", "rUpperArm", "rLowerArm", "rHand", "Torso", "Head"]
    human_capsules.sort()
    
    # Display the plot window
    plt.show()

    
    sample_time = 0.01
    
    try:
        while True:

            data = client.data[-1]


            print(f"\n[DEBUG] Length of data: {len(data)}")
            print(f"[DEBUG] Full data: {data}")
            print(f"[DEBUG] Slice for cap_body (35:91): {data[35:91]}")

            cap_robo = np.array(data[:5*7]).reshape(5, 7)
            cap_body = np.array(data[5*7:(5*7 + 8*7)]).reshape(8, 7)
            
            #print(len(data))
            
            print(data[-36:])
            measured_points = np.array(data[-36:]).reshape(9, 4)
            measured_points = measured_points[:, :3]
                
            # Clear previous plot
            ax1.cla()
            ax2.cla()
            ax3.cla()
            
            # Set plot limits and labels
            if False:
                ax1.set_xlim([-1, 13])
                ax1.set_ylim([-1, 13])
                ax1.set_zlim([-1, 13])
                ax1.set_title('Real-time Robot Data')
                
                # Set plot limits and labels
                ax2.set_xlim([-1, 13])
                ax2.set_ylim([-1, 13])
                ax2.set_zlim([-1, 13])
                ax2.set_title('Real-time Robot Data')
                
                # Set plot limits and labels
                ax3.set_xlim([6, 13])
                ax3.set_ylim([6, 13])
                ax3.set_zlim([6, 13])
                ax3.set_title('Real-time Robot Data')
                
            else:
                ax1.set_xlim([-1, 1])
                ax1.set_ylim([-1, 1])
                ax1.set_zlim([-1, 1])
                ax1.set_title('Real-time Robot Data')
                
                # Set plot limits and labels
                ax2.set_xlim([-1, 1])
                ax2.set_ylim([-1, 1])
                ax2.set_zlim([-1, 1])
                ax2.set_title('Real-time Robot Data')
                
                # Set plot limits and labels
                ax3.set_xlim([-1, 1])
                ax3.set_ylim([-1, 1])
                ax3.set_zlim([-1, 1])
                ax3.set_title('Real-time Robot Data')
            
            # Plot measured_points
            for i in range(measured_points.shape[0]):
                x, y, z = measured_points[i]
                ax1.scatter(x, y, z, s=100, color=colors[i % len(colors)], label=human_joint_names[i])
                
            for i in range(cap_body.shape[0]):
                x1, y1, z1, x2, y2, z2, radius = cap_body[i]
                
                plot_sphere(ax2, x1, y1, z1, radius, color=colors[i])
                plot_sphere(ax2, x2, y2, z2, radius, color=colors[i])
                
                ax3.plot([x1, x2], [y1, y2], [z1, z2], color=colors[i], label=human_capsules[i])
            
            # to get legent in surface plot
            fake_lines = []
            for i in range(len(human_capsules)):
                fake_lines.append(mpl.lines.Line2D([0],[0], linestyle="none", c=colors[i], marker = 'o', label=human_capsules[i]))
            ax2.legend(fake_lines, human_capsules, numpoints = 1)
                
            for i in range(cap_robo.shape[0]):
                x1, y1, z1, x2, y2, z2, radius = cap_robo[i]

                plot_sphere(ax2, x1, y1, z1, radius, color=colors[-1])
                plot_sphere(ax2, x2, y2, z2, radius, color=colors[-1])
                
                ax3.plot([x1, x2], [y1, y2], [z1, z2], color=colors[-1])
                
            ax1.legend()
            ax2.legend()
            ax3.legend()

            # Update the plot
            plt.draw()
            plt.pause(sample_time)
 
    except KeyboardInterrupt:
        pass
    finally:
        stop_thread = True


