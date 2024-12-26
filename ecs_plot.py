import matplotlib.pyplot as plt



seconds = list(range(59))
plt.plot(seconds, esper, label="esper")
plt.plot(seconds, prop, label="prop")
plt.legend()
plt.show()
