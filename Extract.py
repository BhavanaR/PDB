from BeautifulSoup import BeautifulSoup
import urllib2
import urllib
import os
import argparse
import errno
import csv
import traceback
import httplib			
import socket
from collections import defaultdict

time_periods = ["1961-1969","1969-1977"]
pdburl = "https://www.cia.gov/library/readingroom/collection/presidents-daily-brief-{0}?page="
dir_path = os.path.dirname(os.path.realpath(__file__))
timeout = 10
socket.setdefaulttimeout(timeout)

def cli():
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=formatter)

    parser.add_argument(
        '--update_flag',
        action='store_true',
        help='Set true if running the scripts for updation')

    parser.add_argument(
        '--testing',
        action='store_true',
        help='Flag determining if it is a test run.')

    args = parser.parse_args()
    return args.update_flag,args.testing

update_flag,testing = cli()

def print_report(report):

	print "**********Report***************"
	if len(report) == 0:
		print "All PDB files exist in data/ folder. No files downloaded."
	for time_period in report.keys():
		print "TIME PERIOD : {0}".format(time_period)
		print "Total files downloaded : {0}".format(report[time_period]['count'])
		print "Total size of files downloaded : {0}".format(report[time_period]['size'])
	print "**********Report***************"

def download_docs(pdbdocs):
	
	download_dir = dir_path+"/data/"
	meta_data_file = dir_path+"/data/metadata.csv"
	pdb_keys = ['id','name','page_count','link','type','size','time_period']
	if len(pdbdocs) == 0:
		print "No files to download"
		return

	with open(meta_data_file, 'w') as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=pdb_keys,quotechar="'", quoting=csv.QUOTE_MINIMAL, doublequote = True)
		writer.writeheader()
			

	print "Downloading docs to {0}".format(download_dir)
	
	report = {}
	count  = 0
	for pdb in pdbdocs:
		download_path = download_dir + "DOC_{0}.pdf".format(pdb['id'])
		if os.path.exists(download_path):
			print "{0} file exists. Skipping".format(pdb['id'])
			continue

		try:
			os.makedirs(os.path.dirname(download_path))
		except OSError as exc: # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise

		count+=1

		#Writing into meta data file
		with open(meta_data_file, 'a') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=pdb_keys, quotechar="'", quoting=csv.QUOTE_MINIMAL, doublequote = True)
			writer.writerow(pdb)
			
		docfile = urllib.URLopener()
		docfile.retrieve(pdb['link'],download_path)
		
		if 'time_period' not in report:
			report['time_period'] = {}
			report['time_period']['count'] = 0
			report['time_period']['size'] = 0

		report['time_period']['count'] = report['time_period']['count'] + 1
		report['time_period']['size'] += pdb['size']
		if count%20 == 0:
			print "{0} files downloaded".format(count)
	print_report(report)
	
def get_files():
	
	pdbdocs = list()
	
	for time_period in time_periods:
		print "Getting pages for {0} time period".format(time_period)
		page_count = 1
		while True:
			if testing and page_count > 2:
				break
			if page_count % 20 == 0 :
				print "Getting page {0}".format(page_count)
			try :
				html_page = urllib2.urlopen(pdburl.format(time_period)+str(page_count),timeout=5)
			except urllib2.HTTPError, e:
				print 'HTTPError = ' + str(e.code)
			except urllib2.URLError, e:
				print 'URLError = ' + str(e.reason)
			except httplib.HTTPException, e:
				print 'HTTPException'
			except Exception:
				print 'Generic exception: ' + traceback.format_exc()	
			
			soup = BeautifulSoup(html_page)

			content_div = soup.find('div',{'class':'view-content'})
			
			if content_div == None:
				break;

			files_div = content_div.findAll("div",{"class": lambda L: L and L.startswith("views-row")})
			
			
			for div in files_div:
				pdb = {}
					
				title = div.find("div",{"class":"views-field views-field-title"}).text
				pdb['name'] = title

				doc_id = div.find("div",{"class":"views-field views-field-field-document-number"}).find("span",{"class":"field-content"}).text
				pdb['id'] = doc_id

				file_page_count = div.find("div",{"class":"views-field views-field-field-page-count"}).find("div",{"class":"field-content"}).text
				pdb['page_count'] = file_page_count

				link = div.find("div",{"class":"views-field views-field-field-file-1"}).find("a")
				hrefLink = str(link.get('href'))
				pdb['link'] = hrefLink
	
				doc_type = link.get('type').split(';')			
				pdb['type'] = doc_type[0]
				pdb['size'] = int(doc_type[1].split('=')[1])
				
				pdb['time_period'] = time_period
				pdbdocs.append(pdb)
			
			page_count = int(page_count) + 1
	download_docs(pdbdocs)
	
def main():
	get_files()


if __name__ == "__main__":
	main()