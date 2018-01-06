import numpy as np
import gym
import numpy as np

ENV_NAME = 'CartPole-v0'


# Get the environment and extract the number of actions.
env = gym.make(ENV_NAME)
np.random.seed(123)
env.seed(123)
nb_actions = env.action_space.n

print("env.action_space:\n", env.action_space)


env.reset()
for i in range(1000):
    env.render()
    observation, reward, done, info = env.step(env.action_space.sample())
    print(observation,"\n", reward,"\n", done)
    print(info,"\n"+ "="*10)
    if done == True:
    	break

env.close()
print("episode finished")
