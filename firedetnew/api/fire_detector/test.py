import numpy as np
import matplotlib.pyplot as plt

# 从文本文件中读取数据
frame_data = np.loadtxt('frame.txt')

# 将数据重新转换为原始的形状
frame = frame_data.reshape(480, 640, 3).astype(np.uint8)

# 可视化图像
# plt.imshow(frame)
# plt.show()

import numpy as np
import matplotlib.pyplot as plt

# 加载 .npy 文件
rgb_frame = np.load('../../../frame.npy')

# 显示图像
plt.imshow(rgb_frame)
plt.show()
