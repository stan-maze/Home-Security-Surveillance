import numpy as np
import matplotlib.pyplot as plt

# 从文件中加载数组
loaded_arr = np.load('rgb_frame.npy')

# 显示加载的图像
plt.imshow(np.squeeze(loaded_arr, axis=0))
plt.axis('off')
plt.show()
