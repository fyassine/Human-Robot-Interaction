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
    plt.ion()
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    plt.show()

    sample_time = 0.01

    try:
        while True:
            if not client.data:
                time.sleep(sample_time)
                continue

            data = client.data[-1]

            if len(data) < 2 + 36:
                print(f"[WARNING] Skipping frame — expected at least 38 values, got {len(data)}")
                time.sleep(sample_time)
                continue

            joint_positions = np.array(data[2:2+36]).reshape((9, 4))[:, :3]
            print(joint_positions)
            ax.clear()
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_title('Schunk Joint Positions')

            for i in range(len(joint_positions)):
                ax.scatter(joint_positions[i, 0], joint_positions[i, 1], joint_positions[i, 2], c=colors[i], label=human_joint_names[i])

            ax.legend(loc='upper left', bbox_to_anchor=(0, 0.95))
            plt.draw()
            plt.pause(sample_time)

    except KeyboardInterrupt:
        print("Closing plot.")

    finally:
        stop_thread = True
        receiver_thread.join()
        plt.close(fig)
