import dateutil
import json
import traceback
from status.util import SafeHandler


class BioinfoHistoryHandler(SafeHandler):
    def post(self, project_id):
        to_delete = json.loads(self.request.body)
        type = to_delete.get('type', '')
        key = to_delete.get('key', '')

        if type == 'bioinfo-fc':
            db_key = [project_id, key]
            view = self.application.bioinfo_db.view('full_doc/pj_run_to_doc')
        elif type == 'bioinfo-lane':
            # split by the first '-' from the right (to ignore 'ST-' in the flowcell name)
            flowcell_id, lane = key.rsplit('-', 1)
            db_key = [project_id, flowcell_id, lane]
            view = self.application.bioinfo_db.view('full_doc/proj_run_lane_to_doc')
        elif type == 'bioinfo-sample':
            # again here: ignoring 'ST-' in flowcell name (split 2 times, from the right)
            flowcell_id, lane, sample = key.rsplit('-', 2)
            db_key = [project_id, flowcell_id, lane, sample]
            view = self.application.bioinfo_db.view('full_doc/pj_run_lane_sample_to_doc')

        else:
            self.set_status(500)
            answer =  "Unknown entry type:'{}' in bioinfo_history.py ".format(type)
            self.finish(answer)
            return

        rows = view[db_key].rows
        if len(rows) == 0:
            self.set_status(500)
            answer = "Can't access entries with key: '{}' in bioinfo_history.py ".format(' '.join(db_key))
            self.finish(answer)

        deleted_docs = []
        for row in rows:
            doc_id = row.value['_id']
            deleted_docs.append(doc_id)
            try:
                self.application.bioinfo_db.delete(row.value)
            except Exception, e:
                self.set_status(500)
                answer = "Can't delete document: {}. ERROR: {}".format(doc_id, traceback.format_exc(e))
                self.finish(answer)

        self.set_status(200)
        self.write(json.dumps(deleted_docs))