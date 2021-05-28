#!/usr/bin/env python3

# Copyright (c) 2018 Dynamic Robotics Laboratory
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from cassiemujoco import *
from cassiemujoco_ctypes import joint_filter_t, drive_filter_t
import time
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib import cm

MOTOR_POS_IDX = [7,8,9,14,20,21,22,23,28,34]
MOTOR_VEL_IDX = [7,8,9,14,20,21,22,23,28,34]
PASSIVE_VEL_IDX = [9,10,11,14,22,23,24,27]


def euler2quat(z=0, y=0, x=0):

    z = z/2.0
    y = y/2.0
    x = x/2.0
    cz = math.cos(z)
    sz = math.sin(z)
    cy = math.cos(y)
    sy = math.sin(y)
    cx = math.cos(x)
    sx = math.sin(x)
    result =  np.array([
             cx*cy*cz - sx*sy*sz,
             cx*sy*sz + cy*cz*sx,
             cx*cz*sy - sx*cy*sz,
             cx*cy*sz + sx*cz*sy])
    if result[0] < 0:
    	result = -result
    return result

def forwardUpdateClosedLoop(sim, vis, motorPos):
    u = pd_in_t()
    sim.full_reset()
    qpos = sim.qpos()
    qvel = sim.qvel()
    qpos[2] = 2

    for i in range(5):
        qpos[MOTOR_POS_IDX[i]] = motorPos[i]
        qpos[MOTOR_POS_IDX[i+5]] = motorPos[i+5]     
    
    sim.set_qpos(qpos)
    sim.set_qvel(np.zeros((len(qvel), 1)))
    sim.hold()
    nStep = 0
    while nStep < 200:
        J_c = sim.constraint_jacobian()
        err_c = sim.constraint_error()
        J_passive_c = np.zeros(J_c.shape)
        J_passive_c[:, PASSIVE_VEL_IDX] = J_c[:, PASSIVE_VEL_IDX]
        # print('\nJ_passive_c')
        # print(J_passive_c.shape)
        # print(J_passive_c)
        # print('\nJ_c Full')
        # print(J_c.shape)
        # print(J_c)
        # print('\nerr_c')
        # print(err_c.shape)
        # print(err_c)
        q_vel = np.linalg.lstsq(J_passive_c, -200*err_c, rcond=None)
        # print('\nq_vel')
        # print(q_vel[0].shape)
        # print(q_vel[0])
        sim.set_qvel(q_vel[0])
        sim.integrate_pos()

        nStep = nStep + 1  
        draw_state = vis.draw(sim)

    qpos_final = sim.qpos()
    for i in range(10):
        print("idx " + str(i) + "   des: " + str(motorPos[i]) + "  Final: " + str(qpos_final[MOTOR_POS_IDX[i]]))
    return qpos_final

# Initialize cassie simulation
sim = CassieSim("../model/cassie_no_grav.xml")
print(sim.nq)
vis = CassieVis(sim)

# Set control parameters
u = pd_in_t()

# Record time
t = time.monotonic()
count = 0

# Run until window is closed or vis is quit
draw_state = vis.draw(sim)

sim.full_reset()
qpos = sim.qpos()
motor_pos = []
for i in range(10):
    motor_pos.append(qpos[MOTOR_POS_IDX[i]])

N_grid = 30
# hip_list = np.radians(np.linspace(-50, 80, num=N_grid))
# knee_list = np.radians(np.linspace(-156, -42, num=N_grid))


hip_list = np.radians(np.linspace(-20, 60, num=N_grid))
knee_list = np.radians(np.linspace(-100, -60, num=N_grid))

error = np.zeros((N_grid,N_grid))

for left_hip_idx in range(N_grid):
    for left_knee_idx in  range(N_grid):

        left_hip_pitch_angle = hip_list[left_hip_idx]
        left_knee_angle = knee_list[left_knee_idx]
        # sim.full_reset()
        # qpos = sim.qpos()
        # qpos[MOTOR_POS_IDX[2]] = left_hip_pitch_angle
        # qpos[MOTOR_POS_IDX[3]] = left_knee_angle
        # qpos[MOTOR_POS_IDX[7]] = left_hip_pitch_angle
        # qpos[MOTOR_POS_IDX[8]] = left_knee_angle
        # sim.set_qpos(qpos)
        # draw_state = vis.draw(sim)
        # time.sleep(1/30)
        motor_pos[2] = left_hip_pitch_angle
        motor_pos[3] = left_knee_angle
        motor_pos[7] = left_hip_pitch_angle
        motor_pos[8] = left_knee_angle
        
        qpos_result = forwardUpdateClosedLoop(sim, vis, motor_pos)
        error[left_hip_idx, left_knee_idx] =   np.sqrt((left_hip_pitch_angle - qpos_result[MOTOR_POS_IDX[2]])**2 + (left_hip_pitch_angle - qpos_result[MOTOR_POS_IDX[2]])**2)


# Plot the surface.

fig, axs = plt.subplots(nrows=1, ncols=1)
temp_imshow = axs.imshow(error, extent = (hip_list[0], hip_list[-1], knee_list[0], knee_list[-1]))

fig.colorbar(temp_imshow, ax=axs)

plt.show()

print(error)


