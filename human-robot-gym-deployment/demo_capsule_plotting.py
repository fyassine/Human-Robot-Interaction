#!/usr/bin/env python
"""This script is used to test UDP execution and visualize joint positions from the Schunk robot.

Assumes only 38 values are received per packet:
- First 2: ignored
- Next 36: 9 joints × (x, y, z, w) → we use only (x, y, z)

Creator:
    Jakob Thumm
"""

from communi_cat.client_cat import ClientCat
import matplotlib.pyplot as plt
import numpy as np
import threading
import time

# Plot settings
colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown', 'pink', 'cyan', 'yellow', 'black', 'gray']
human_joint_names = ["lShoulder", "lElbow", "lHand", "rShoulder", "rElbow", "rHand", "Collar", "Torso", "Head"]

# Threaded UDP data receiving
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
    # plt.ion()
    # fig = plt.figure(figsize=(6, 6))
    # ax = fig.add_subplot(111, projection='3d')
    # plt.show()

    sample_time = 0.01

    try:
        while True:
            print("data_received", client.data)
            data = client.data[-1]

            if len(data) < 2 + 36:
                print(f"[WARNING] Skipping frame — expected at least 38 values, got {len(data)}")
                time.sleep(sample_time)
                continue

            joint_data = data[2:2+36]  # Skip first 2
            measured_points = np.array(joint_data).reshape(9, 4)[:, :3]  # Use only x, y, z
            print(measured_points)
            # ax.cla()
            # ax.set_xlim([-1, 1])
            # ax.set_ylim([-1, 1])
            # ax.set_zlim([-1, 1])
            # ax.set_title("Real-time Joint Positions")

            # for i in range(measured_points.shape[0]):
            #     x, y, z = measured_points[i]
            #     ax.scatter(x, y, z, s=100, color=colors[i % len(colors)], label=human_joint_names[i])

            # ax.legend()
            # plt.draw()
            plt.pause(sample_time)

    except KeyboardInterrupt:
        pass
    finally:
        stop_thread = True
