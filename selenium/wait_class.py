class element_has_attribute(object):
  def __init__(self, locator, attribute, attribute_value):
    self.locator = locator
    self.attribute = attribute
    self.attribute_value = attribute_value

  def __call__(self, driver):
    element = driver.find_element(*self.locator)   # Finding the referenced element
    if element.get_attribute(self.attribute) != self.attribute_value:
      return False
    else:
      return True
      