class RefreshExperimentsHandler(BaseHandler):
"""Handles periodic refresh for a scheduled task with cron for AppEngine."""

  def get(self):
    experiments = get_experiments()
    update_experiments_db(experiments)


def get_experiments():
  """Queries the Management API for all active experiments."""
  try:
    experiments = ANALYTICS_SERVICE.management().experiments().list(
        accountId='1234',
        webPropertyId='UA-1234-1',
        profileId='56789').execute()
  except TypeError, error:
    # Handle errors in constructing a query.
    logging.error('There was an error constructing the query : %s' % error)
  except HttpError, error:
    # Handle API errors.
    logging.error('API error : %s : %s' % (error.resp.status,
                                           error._get_reason()))
  return experiments

def update_experiments_db(experiments):
  """Updates the datastore with the provided experiment data.

    Args:
      experiments: A list of experiments.
  """
  if experiments:
    for experiment in experiments.get('items', []):
      experiment_key = db.Key.from_path('Experiment', experiment.get('id'))
      experiment_db = db.get(experiment_key)

      # Update experiment values
      experiment_db.status = experiment.get('status')
      experiment_db.start_time = experiment.get('startTime')
      ... # Continue to update all properties

      # Update memcache with the experiment values.
      memcache.set(experiment.get('id'), experiment)

      # Update Variations
      for index, variation in enumerate(experiment.get('variations', [])):
        variation_db = experiment_db.variations.get_by_id(index)
        variation_db.status = variation.get('status')
        variation_db.weight = variation.get('weight')
        variation_db.won = variation.get('won')
        ... # Continue updating variation properties
        variation_db.put()

      experiment_db.put()