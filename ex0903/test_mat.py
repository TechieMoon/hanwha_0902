# matplotlib 산점도(scatter) 연습
import matplotlib.pyplot as plt
import numpy as np

# x, y: 점 13개의 좌표 (두 배열의 길이가 같아야 한다)
x = np.array([5,7,8,7,2,17,2,9,4,11,12,9,6])
y = np.array([99,86,87,88,111,86,103,87,94,78,77,85,86])
# 점마다 다른 색을 주려고 만든 배열. 지금은 scatter에 넘기지 않아서 쓰이지 않는다.
# 점마다 색을 입히려면 plt.scatter(x, y, c=colors)
colors = np.array(["red","green","blue","yellow","pink","black","orange","purple","beige","brown","gray","cyan","magenta"])

plt.scatter(x,y)  # 점 찍기

plt.show()  # 창으로 그래프 띄우기
