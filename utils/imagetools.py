'''functions for splitting up images and recombining them based on focus
core by yujie --- 4/4/2020
'''

import cv2
import numpy as np

''' Returns color IMG broken into BLOCK_DIMS[0]xBLOCK_DIMS[1] 
    sub-rectangles as 5-dimensional array of NEW_X, NEW_Y, X,
    Y, CHANNEL. '''
def partition_image(img, block_dims = (4,4)):
  if (len(img.shape) == 2):
    yield from partition_gray(img, block_dims)
    return
  x_len, y_len, channels = img.shape
  x_block, y_block = block_dims
  for x in range(0, x_len - x_len % x_block, x_block):
    for y in range(0, y_len - y_len % y_block, y_block):
      yield img[x : x + x_block, y : y + y_block, :]

''' Returns cv2 grayscale IMG broken into BLOCK_DIMS[0]x
    BLOCK_DIMS[1] sub-rectangles as 4-dimensional array 
    of NEW_X, NEW_Y, X, Y. '''
def partition_gray(img, block_dims = (4,4)):
  x_len, y_len = img.shape
  x_block, y_block = block_dims
  for x in range(0, x_len - x_len % x_block, x_block):
    for y in range(0, y_len - y_len % y_block, y_block):
      yield img[x : x + x_block, y : y + y_block]

''' Yields 4^depth color sub-IMG, in up-down, 
    left-right order.'''
def quadtree_split(img, depth = 1):
  assert depth >= 0, 'invalid args'
  assert hasattr(img, 'shape'), 'invalid'
  if(len(img.shape) == 2):
    yield from gray_quadtree_split(img, depth)
    return
  if (depth == 0):
    yield img
  else:
    y1x1 = quadtree_split(image_quarter(img, 0), depth - 1)
    y2x1 = quadtree_split(image_quarter(img, 1), depth - 1)
    for y in range(0, 2 ** (depth - 1)):
      yield from yield_until(y1x1, 2 ** (depth - 1))
      yield from yield_until(y2x1, 2 ** (depth - 1))
    y1x2 = quadtree_split(image_quarter(img, 2), depth - 1)
    y2x2 = quadtree_split(image_quarter(img, 3), depth - 1)
    for y in range(0, 2 ** (depth - 1)):
      yield from yield_until(y1x2, 2 ** (depth - 1))
      yield from yield_until(y2x2, 2 ** (depth - 1))

''' Returns a quarter of IMG up-down, left-right'''
def image_quarter(img, number):
  x_len, y_len, channels = img.shape
  if (number == 0):
    return img[0 : x_len // 2, 0 : y_len // 2, :]
  elif (number == 1):
    return img[x_len // 2 : x_len - x_len % 2, 
    0 : y_len // 2, :]
  elif (number == 2):
    return img[0 : x_len // 2, y_len // 2 :
    y_len - y_len % 2, :]
  else:
    return img[x_len // 2 : x_len - x_len % 2,
    y_len // 2 : y_len - y_len % 2, :]

''' Yield from ITER LIMIT times. '''
def yield_until(iter, limit):
  for i in range(limit):
    yield next(iter)

''' Returns laplacian float representing blurriness '''
def calculate_sharp(frame):
   return cv2.Laplacian(frame, cv2.CV_64F).var()

''' Returns the maximum image specified by KEY '''
def max_images(images, key = calculate_sharp):
  values = list(map(calculate_sharp, images))
  index_max = max(range(len(values)), key=values.__getitem__)
  return images[index_max]
  # best_image, best_val = images[0], calculate_sharp(best_image)
  # for i in range(1, len(images)):
  #   curr_val = calculate_sharp(images[i])
  #   if curr_val > best_val:

''' Selects the max of iterators of images, producing final image of size
    FINAL_DIMS[0]xFINAL_DIMS[1]. '''
def reconstruct_max(list_iterators, final_dims, key = calculate_sharp):
  list_sub_images = [next(image_gen) for image_gen in list_iterators]
  prev_images = max_images(list_sub_images, key = calculate_sharp)
  for y in range(1 ,final_dims[1], 1):
    list_sub_images = [next(image_gen) for image_gen in list_iterators]
    best_image = max_images(list_sub_images, key = calculate_sharp)
    prev_images = np.concatenate((prev_images, best_image), axis = 1)
  prev_row = prev_images
  for x in range(1, final_dims[0], 1):
    list_sub_images = [next(image_gen) for image_gen in list_iterators]
    prev_images = max_images(list_sub_images, key = calculate_sharp)
    for y in range(1 ,final_dims[1], 1):
      list_sub_images = [next(image_gen) for image_gen in list_iterators]
      best_image = max_images(list_sub_images, key = calculate_sharp)
      prev_images = np.concatenate((prev_images, best_image), axis = 1)
    prev_row = np.concatenate((prev_row, prev_images), axis = 0)
  return prev_row

''' Returns an image from a combined iterable IMAGES, subdivided into 
##    IMAGES.SHAPE[0]//4 x IMAGES.SHAPE[1]//4 '''
def max_pool_subdivided_images(images, subdiv_dims = (4, 4)):
  subdiv_x, subdiv_y = subdiv_dims
  subimage_generators = [partition_image(image, (image.shape[0] // subdiv_x, 
    image.shape[1] // subdiv_y)) for image in images]
  best_image = reconstruct_max(subimage_generators, (subdiv_x, subdiv_y))
  return best_image

''' Convert FRAME into pure black/white where black is outside color bounds
    and white is inside color bounds'''
def frame_hue_bounded(frame, lower_bound = np.array([20, 100, 100]), 
  upper_bound = np.array([30, 255, 255])):
  hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
  return cv2.inRange(hsv, lower_bound, upper_bound)
