# -*- coding: utf-8 -*-
"""Export processing results to Timesketch."""

from __future__ import print_function
from __future__ import unicode_literals

from dftimewolf.lib import timesketch_utils
from dftimewolf.lib import module


class TimesketchExporter(module.BaseModule):
  """Exports a given set of plaso or CSV files to Timesketch.

  input: A list of paths to plaso or CSV files.
  output: A URL to the generated timeline.
  """

  def __init__(self, state):
    super(TimesketchExporter, self).__init__(state)
    self.timesketch_api = None
    self.incident_id = None
    self.sketch_id = None

  def setup(self,  # pylint: disable=arguments-differ
            endpoint=None,
            username=None,
            password=None,
            incident_id=None,
            sketch_id=None):
    """Setup a connection to a Timesketch server and create a sketch if needed.

    Args:
      endpoint: str, Timesketch endpoint (e.g. http://timesketch.com/)
      username: str, Username to authenticate against the Timesketch endpoint.
      password: str, Password to authenticate against the Timesketch endpoint.
      incident_id: str, Incident ID or reference. Used in sketch description.
      sketch_id: int, Sketch ID to add the resulting timeline to. If not
          provided, a new sketch is created.
    """
    self.timesketch_api = timesketch_utils.TimesketchApiClient(
        endpoint, username, password)
    self.incident_id = None
    self.sketch_id = int(sketch_id) if sketch_id else None

    # Check that we have a timesketch session
    if not self.timesketch_api.session:
      message = 'Could not connect to Timesketch server at ' + endpoint
      self.state.add_error(message, critical=True)
      return

    if not self.sketch_id:  # No sketch id is provided, create it
      if incident_id:
        sketch_name = 'Sketch for incident ID: ' + incident_id
      else:
        sketch_name = 'Untitled sketch'
      sketch_description = 'Sketch generated by dfTimewolf'

      self.sketch_id = self.timesketch_api.create_sketch(
          sketch_name, sketch_description)
      print('Sketch {0:d} created'.format(self.sketch_id))

  def cleanup(self):
    pass

  def process(self):
    """Executes a Timesketch export."""
    # This is not the best way of catching errors, but timesketch_utils will be
    # deprecated soon.
    # TODO(tomchop): Consider using the official Timesketch python API.
    if not self.timesketch_api.session:
      message = 'Could not connect to Timesketch server'
      self.state.add_error(message, critical=True)

    named_timelines = []
    for description, path in self.state.input:
      if not description:
        description = 'untitled timeline for '+path
      named_timelines.append((description, path))
    try:
      self.timesketch_api.export_artifacts(named_timelines, self.sketch_id)
    except RuntimeError as e:
      self.state.add_error(
          'Error occurred while working with Timesketch: {0:s}'.format(str(e)),
          critical=True)
      return
    sketch_url = self.timesketch_api.get_sketch_url(self.sketch_id)
    print('Your Timesketch URL is: {0:s}'.format(sketch_url))
    self.state.output = sketch_url
