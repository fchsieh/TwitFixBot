import sys

from gallery_dl import config, exception, job, util


class GalleryDL(job.DataJob):
    def __init__(self, url, parent=None, file=sys.stdout):
        job.DataJob.__init__(self, url, parent)

    def run(self):
        extractor = self.extractor
        sleep = util.build_duration_func(extractor.config("sleep-extractor"))
        if sleep:
            extractor.sleep(sleep(), "extractor")

        # collect data
        try:
            for msg in extractor:
                self.dispatch(msg)
        except exception.StopExtraction:
            pass
        except Exception as exc:
            self.data.append((exc.__class__.__name__, str(exc)))
        except BaseException:
            pass

        # convert numbers to string
        if config.get(("output",), "num-to-str", False):
            for msg in self.data:
                util.transform_dict(msg[-1], util.number_to_string)
