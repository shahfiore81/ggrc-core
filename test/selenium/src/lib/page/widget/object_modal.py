# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Modals for creating / making changes to objects:
* New object
* Edit object
* Proposal for object
"""
from lib import base
from lib.entities import entity
from lib.page.modal import unified_mapper


def get_modal_obj(obj_type, selenium):
  """Gets modal obj for `obj_type`."""
  mapping = {
      "assessment": AssessmentModal,
      "control": ControlModal
  }
  return mapping.get(obj_type.lower(), BaseObjectModal)(selenium)


_FIELD_METHOD_MAPPING = {
    "title": "set_title",
    "description": "set_description",
    "status": "set_state",
    "slug": "set_code",
    "assertions": "select_assertions",
    "mapped_objects": "map_objects"
}


class BaseObjectModal(base.WithBrowser):
  """Represents object modal."""

  def __init__(self, driver):
    super(BaseObjectModal, self).__init__(driver)
    self._root = self._browser.element(css=".modal[style*='display: block']")
    self.title_field = self._root.text_field(name="title")
    self.description_field = self._root.div(
        data_placeholder="Enter Description")
    self.state_select = self._root.select(can_value="instance.status")
    self.code_field = self._root.text_field(name="slug")
    self._fields = ["title", "description", "status", "slug"]

  def submit_obj(self, obj):
    """Submits form with `obj`."""
    obj_dict = obj.__dict__
    fields_dict = {k: obj_dict[k] for k in self._fields}
    self.fill_form(**fields_dict)
    self.save_and_close()

  def fill_form(self, **fields_dict):
    """Fills form with values from `fields_dict`."""
    for key, value in fields_dict.iteritems():
      if value is not None:
        getattr(self, _FIELD_METHOD_MAPPING[key])(value)

  def save_and_close(self):
    """Clicks Save & Close button and waits for changes to happen."""
    self._root.link(data_toggle="modal-submit", text="Save & Close").click()
    self._root.element(class_name="spinner").wait_until_not_present()

  def set_title(self, title):
    """Sets title."""
    self.title_field.set(title)

  def set_description(self, description):
    """Sets description."""
    self.description_field.send_keys(description)

  def set_state(self, state):
    """Sets value in state dropdown."""
    self.state_select.select(state)

  def set_code(self, code):
    """Sets code."""
    self.code_field.set(code)


class ControlModal(BaseObjectModal):
  """Represents control object modal."""

  def __init__(self, driver):
    super(ControlModal, self).__init__(driver)
    self._fields = ["title", "description", "status", "slug", "assertions"]

  def select_assertions(self, assertions):
    """Selects assertions."""
    multi_select_root = self._root.element(data_id="assertions_dd")
    # Chromedriver's `click` isn't able to work with these elements
    multi_select_root.element(
        class_name="multiselect-dropdown__input").js_click()
    for assertion in assertions:
      multi_select_root.checkbox(id=str(assertion["id"])).js_click()


class AssessmentModal(BaseObjectModal):
  """Represents assessment object modal."""

  def __init__(self, driver):
    super(AssessmentModal, self).__init__(driver)
    self._fields = ["title", "description", "slug", "mapped_objects"]

  def map_objects(self, objs):
    """Maps objects using `Map Objects` button."""
    objs = [entity.Representation.repr_dict_to_obj(obj)
            if isinstance(obj, dict) else obj for obj in objs]
    # Ordinary `click()` doesn't work in headless Chrome in this case
    self._root.element(class_name="assessment-map-btn").js_click()
    mapper = unified_mapper.AssessmentCreationMapperModal(
        self._driver, "assessments")
    mapper.map_dest_objs(
        dest_objs_type=objs[0].type,
        dest_objs_titles=[obj.title for obj in objs])

  def get_mapped_snapshots_titles(self):
    """Gets titles of mapped snapshots."""
    els = self._root.elements(class_name="modal-mapped-objects-item")
    return [el.element(class_name="title").text for el in els]
