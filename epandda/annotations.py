import re
from mongo import mongoBasedResource

#
#
#
class annotations(mongoBasedResource):
    def process(self):

        # Mongodb index for Publication
        annotations = self.client.endpoints.annotations
  
        # returns dictionary of params as defined in endpoint description
        # will throw exception if required param is not present
        params = self.getParams()
        
        # offset and limit returned as ints with default if not set
        offset = self.offset()
        limit = self.limit()

        if limit < 1:
          limit = 100

        annoQuery = []
        if self.paramCount > 0:

          criteria = {
            'endpoint': 'annotations',
            'parameters': {},
          }

          for p in ['annotationDate', 'annotationDateAfter', 'annotationDateBefore']:  
 
            if params[p]:

              if 'annotationDate' == p:
                annoQuery.append({"annotatedAt": { '$regex': params[p]} })

              if 'annotationDateAfter' == p:
                annoQuery.append({"annotatedAt": { '$gte': params[p]} }) 
            
              if 'annotationDateBefore' == p:
                print "annotation Date Before: " + str(params[p])
                annoQuery.append({"annotatedAt": { '$lte': params[p]} })

              criteria['parameters'][p] = str(params[p]).lower()

          d = []
 
          # Total Count:
          annoCount = annotations.find({}).count()

          if annoQuery:
            res = annotations.find({"$and":  annoQuery }, {'_id': False}).skip(offset).limit(limit)
            annoCount = res.count()

          else:
            # Allows for optional Date param since you can't $and on nothing.
            res = annotations.find({}, {'_id': False}).skip(offset).limit(limit)
            


          if res:
              for i in res:
                  d.append(i)


          counts = {'totalCount': annoCount, 'annotationsCount': len(d)}

          return self.respond({
              'counts': counts, 
              'results': d,
              'criteria': criteria,
          })
        else:

          return self.respondWithDescription()
            

    def description(self):
        return {
            'name': 'Annotations',
            'maintainer': 'Jon Lauters',
            'maintainer_email': 'jon@epandda.org',
            'description': 'Returns openAnnotations for linked data in ePANDDA.',
            'params': [
                {
                    "name": "annotationDate",
                    "label": "Annotation Date",
                    "type": "text",
                    "required": False,
                    "description": "Filter annotation results by provided date ( simple date match ). Format annotationDate=YYYY-MM-DD"
                },
                {
                    "name": "annotationDateAfter",
                    "label": "Annotation Date After",
                    "type": "text",
                    "required": False,
                    "description": "Filter annotation results equal to or after provided date. Format annotationDateAfter=YYYY-MM-DD"
                },
                {
                    "name": "annotationDateBefore",
                    "label": "Annotation Date Before",
                    "type": "text",
                    "required": False,
                    "description": "Filter annotation results before provided date. Format annotationDateBefore=YYYY-MM-DD"
                }
            ]
        }
                
