from mongo import mongoBasedResource
from flask_restful import reqparse
import gridfs
import json

parser = reqparse.RequestParser()

# Add Arguments (params) to parser here ...
parser.add_argument('scientific_name', type=str, help='Taxonomic name to search occurrences for')
parser.add_argument('locality', type=str, help='Locality name to filter taxonomic occurrences by')
parser.add_argument('period', type=str, help='The geologic time period to filter taxonomic occurrences by')
parser.add_argument('institution_code', type=str, help='The abbreviated code submitted by data provider to filter taxonomic occurrences by')

#
#
#
class occurrences(mongoBasedResource):
	def process(self):
	
		lindex = self.client.endpoints.localityIndex2                       # Mongodb index for localities
		tindex = self.client.endpoints.taxonIndex						   # Mongodb index for taxonomies
		
		grid = gridfs.GridFS(self.client.endpoints)                   

		# returns dictionary of params as defined in endpoint description
		# will throw exception if required param is not present
		params = self.getParams()
		# offset and limit returned as ints with default if not set
		offset = self.offset()
		limit = self.limit()

		if self.paramCount > 0:
			localityRes = None
			res = None
			criteria = {'endpoint': 'taxonomy', 'parameters': {}, 'matchTerms': {'scientificNames': [], 'stateProvinceNames': [], 'countryNames': [], 'countyNames': [], 'localityNames': [], 'originalStates': [], 'originalCountries': [], 'originalCounties': [], 'originalLocalities': []}}
			taxonQuery = []
			localityQuery = []
			instQuery = []
			stratQuery = []
			if params['taxon_name']:
				taxon_name = params['taxon_name']
				res = tindex.find({"$text": {"$search": '"' + taxon_name + '"'}})
			
			if params['locality']:
				locality = params['locality']
				localityRes = lindex.find({'$text': {'$search': '"' + locality + '"'}})
			
			# TODO: Add Filtering for locality, period and institution
			d = []
			matches = {'idigbio': [], 'pbdb': []}
			taxonMatches = {'idigbio': [], 'pbdb': []}
			idbCount = 0
			pbdbCount = 0
			if res:
				for i in res:
					for i in res:
						taxonomy = i['taxonomy']
						scientificNames = i['scientificNames']
						for sciName in scientificNames:
							if sciName not in criteria['matchTerms']['scientificNames']:
								criteria['matchTerms']['scientificNames'].append(sciName)
						taxon_ranks = taxonomy.keys()
						for rank in taxon_ranks:
							if rank in criteria['matchTerms']:
								for term in taxonomy[rank]:
									if term not in criteria['matchTerms'][rank]:
										criteria['matchTerms'][rank].append(term)
							else:
								criteria['matchTerms'][rank] = []
								for term in taxonomy[rank]:
									criteria['matchTerms'][rank].append(term)

						if 'pbdbGridFile' in i:
							pbdbGrids = i['pbdbGridFile']
							for file in pbdbGrids:
								pbdb_doc = grid.get(file)
								pbdb_matches = json.loads(pbdb_doc.read())
								taxonMatches['pbdb'] = taxonMatches['pbdb'] + pbdb_matches

						if 'idbGridFile' in i:
							if type(i['idbGridFile']) is list:
								idbGrids = i['idbGridFile']
								for file in idbGrids:
									idb_doc = grid.get(file)
									idb_matches = json.loads(idb_doc.read())
									taxonMatches['idigbio'] = taxonMatches['idigbio'] + idb_matches
							else:
								idb_doc = grid.get(i['idbGridFile'])
								idb_matches = json.loads(idb_doc.read())
								taxonMatches['idigbio'] = taxonMatches['idigbio'] + idb_matches
			geoMatches = {'idigbio': [], 'pbdb': []}
			if localityRes:
				for i in localityRes:
					if 'countryName' in i and i['countryName'] not in criteria['matchTerms']['countryNames']:
						criteria['matchTerms']['countryNames'].append(i['countryName'])
					if 'stateProvinceName' in i and i['stateProvinceName'] not in criteria['matchTerms']['stateProvinceNames']:
						criteria['matchTerms']['stateProvinceNames'].append(i['stateProvinceName'])
					if 'county' in i and i['county'] not in criteria['matchTerms']['countyNames']:
						criteria['matchTerms']['countyNames'].append(i['county'])
					if 'locality' in i:
						if i['locality'] not in criteria['matchTerms']['localityNames']:
							criteria['matchTerms']['localityNames'].append(i['locality'])
						
					if 'originalStateProvinceName' in i:
						for origState in i['originalStateProvinceName']:
							if origState not in criteria['matchTerms']['originalStates']:
								criteria['matchTerms']['originalStates'].append(origState)
					if 'originalCountryName' in i:
						for origCountry in i['originalCountryName']:
							if origCountry not in criteria['matchTerms']['originalCountries']:
								criteria['matchTerms']['originalCountries'].append(origCountry)
					if 'original_country' in i:
						for origCounty in i['original_county']:
							if origCounty not in criteria['matchTerms']['originalCounties']:
								criteria['matchTerms']['originalCounties'].append(origCounty)
					if 'original_locality' in i:
						for origLocality in i['original_locality']:
							if origCounty not in criteria['matchTerms']['originalLocalities']:
								criteria['matchTerms']['originalLocalities'].append(origLocality)
					if 'pbdbGridFile' in i:
						if type(i['pbdbGridFile']) is list:
							pbdbGrids = i['pbdbGridFile']
							for file in pbdbGrids:
								pbdb_doc = grid.get(file)
								pbdb_matches = json.loads(pbdb_doc.read())
								geoMatches['pbdb'] = geoMatches['pbdb'] + pbdb_matches
						else:
							idb_doc = grid.get(i['idbGridFile'])
							idb_matches = json.loads(idb_doc.read())
							geoMatches['idigbio'] = geoMatches['idigbio'] + idb_matches
								
					if 'idbGridFile' in i:
						if type(i['idbGridFile']) is list:
							idbGrids = i['idbGridFile']
							for file in idbGrids:
								idb_doc = grid.get(file)
								idb_matches = json.loads(idb_doc.read())
								geoMatches['idigbio'] = geoMatches['idigbio'] + idb_matches
						else:
							idb_doc = grid.get(i['idbGridFile'])
							idb_matches = json.loads(idb_doc.read())
							geoMatches['idigbio'] = geoMatches['idigbio'] + idb_matches
				
			idbGeoSet = set(geoMatches['idigbio'])
			pbdbGeoSet = set(geoMatches['pbdb'])
			idbTaxonSet = set(taxonMatches['idigbio'])
			pbdbTaxonSet = set(taxonMatches['pbdb'])
			#return {'idbGeo': len(geoMatches['idigbio']), 'pbdbGeo': len(geoMatches['pbdb']), 'idbTaxon': len(taxonMatches['idigbio']), 'pbdbTaxon': len(taxonMatches['pbdb'])}
			#return {'idbGeo': list(idbGeoSet), 'pbdbGeo': list(pbdbGeoSet), 'idbTaxon': list(idbTaxonSet), 'pbdbTaxon': list(pbdbTaxonSet)}
			matches['idigbio'] = list(idbGeoSet & idbTaxonSet)
			matches['pbdb'] = list(pbdbGeoSet & pbdbTaxonSet)
			return matches
			idbCount = len(matches['idigbio'])
			pbdbCount = len(matches['pbdb'])

			item = {'matches': {'idigbio': matches['idigbio'], 'pbdb': matches['pbdb']}}
			d.append(item)
			d = self.resolveReferences(d)
			counts = {'totalCount': idbCount + pbdbCount, 'idbCount': idbCount, 'pbdbCount': pbdbCount}
			d['pbdb_resolved'] = d['pbdb_resolved'][offset:limit]
			return self.respond({'counts': counts, 'results': d, 'criteria': criteria})
		else:
			return self.respondWithDescription()


	def description(self):
		return {
			'name': 'Occurrence index',
			'maintainer': 'Michael Benowitz',
			'maintainer_email': 'michael@epandda.org',
			'description': 'Returns specimens collected from a given locality',
			'params': [
				{
					"name": "taxon_name",
					"type": "text",
					"required": True,
					"description": "The taxa to search occurrences for"
				},
				{
					"name": "locality",
					"type": "text",
					"required": False,
					"description": "The locality name to bound taxonomic occurences to",
				},
				{
					"name": "period",
					"type": "text",
					"description": "The geologic time period to filter taxon occurrences by"
				},
				{
					"name": "institution_code",
					"type": "text",
					"char_limit": "TBD",
					"description": "The abbreviated institution code that houses the taxon occurrence specimen"
				}
			]}