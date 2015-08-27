import json
import urllib, urllib2

BING_API_KEY = ''

def run_query(search_terms):
	# Specify base
	root_url = 'https://api.datamarket.azure.com/Bing/Search/'
	source = 'Web'

	# Specify how many results we wish to be returned per page
	# Offset specifies where in the results list to start from
	# With results_per_page = 10 and offset = 11, this would start from page 2
	results_per_page = 10
	offset = 0

	# Wrap quotes around our query terms as required by the Bing API 
	# The query we will then use is stored within variable query
	query = "'{0}'".format(search_terms)
	query = urllib.quote(query)

	# Construct the latter part of our request's URL 
	# Sets the format of the response to JSON and sets other properties 
	search_url = "{0}{1}?$format=json&$top={2}&$skip={3}&Query={4}".format(
		root_url,
		source,
		results_per_page,
		offset,
		query)

	username = ''

	password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
	password_mgr.add_password(None, search_url, username, BING_API_KEY)

	results = []

	try:
		handler = urllib2.HTTPBasicAuthHandler(password_mgr)
		opener = urllib2.build_opener(handler)
		urllib2.install_opener(opener)

		response = urllib2.urlopen(search_url).read()

		json_response = json.loads(response)
		
		print json_response

		for result in json_response['d']['results']:
			results.append({'title':result['Title'], 
							'link': result['Url'],
							'summary': result['Description']})

	except urllib2.URLError, e:
		print "Error when querying the Bing API: ", e

	return results 

def main():
	usr_input = input('Enter your query...please use quotes: ')
	results = run_query(usr_input)
	for result in results:
		print 'Title: ' + result['title']
		print 'Link: '+result['link']
		print 'Summary: '+result['summary']
	return

if __name__ == '__main__':
	main()