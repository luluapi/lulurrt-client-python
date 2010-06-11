# coding=utf-8
"""
Python client library for Lulu Ratings & Reviews API
http://developer.lulu.com/docs/RatingReviews

"""

__licence__ = """
Copyright 2009-2010 Lulu, Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License. You may
obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
    implied. See the License for the specific language governing
    permissions and limitations under the License.
"""
import sys
import time
import hashlib
import urllib, urllib2
import simplejson as json

class InvalidInput(Exception):
  pass
class ServiceError(Exception):
  pass

class WrservicesJSONClient:
  def __init__(self, service, version, api_key, secret, endpoints={}):
    host = 'apps.lulu.com'
    self.url_format = "http://%s/services/%s/%s/%%s" % (host, service, version)
    self.qstring_sep = '?'
    self.api_key = api_key
    self.secret = secret
    if len(endpoints):
      self.endpoints = endpoints
    
    if api_key.strip():
      self.url_format = self.url_format + '?api_key=' + urllib.quote(api_key)
      self.qstring_sep = '&'

  def get_signature(self, fname):
    if 'endpoints' not in self.__dict__:
      return "No signatures available"
    if fname not in self.endpoints:
      return "%s is not a valid method for this service" % fname
    else:
      return "%s(%s)" % (fname, ", ".join(self.endpoints[fname]))

  def __call__(self, *args, **kwargs):
    args = list(args)
    kwargs = kwargs.copy()
    
    fname = self.fname
    url_format = self.url_format
    qstring_sep = self.qstring_sep
    api_key = self.api_key
    secret = self.secret

    if 'endpoints' in self.__dict__:
      if len(args) != len(self.__dict__['endpoints'][fname]) and len(kwargs) == 0:
        raise TypeError("%s expected %d arguments, got %d" %
                        (fname, len(self.__dict__['endpoints'][fname]), len(args)))
      else:
        unexpected = set(kwargs.keys()) - set(self.__dict__['endpoints'][fname])
        if len(unexpected):
          raise TypeError("%s got an unexpected keyword argument" % fname)
        if len(kwargs) != len(self.__dict__['endpoints'][fname]):
          raise TypeError("%s expected %d arguments, got %d" %
                          fname, len(self.__dict__['endpoints'][fname]), len(kwargs))

    if len(args) > 0:
      kwargs['args'] = args
    
    for key, value in kwargs.items():
      kwargs[key] = json.dumps(value)

    sig_text = "%s%s%s" % (api_key, secret, int(time.time()))
    sig = hashlib.sha256(sig_text).hexdigest()
    kwargs['sig'] = sig

    base_url = url_format % (fname)
    
    qstring = urllib.urlencode(kwargs)
    try:
      if fname.startswith(("add", "post", "submit", "set", "update", "delete")):
        req = urllib2.Request(base_url, qstring)
      else:
        req = urllib2.Request(base_url + qstring_sep + qstring)
      
      response = urllib2.urlopen(req).read()
    except urllib2.HTTPError, e:
      raise ServiceError("Error connecting to webservice. HTTP-%d: %s"
              % (e.code, e))
    except urllib2.URLError, e:
      raise ServiceError("Error connecting to webservice. %s" % e)
    
    try:
      response = json.loads(response)['response']
    except (TypeError, ValueError, UnicodeError, AttributeError), e:
      raise ServiceError("Couldn't decode response from webservice. %s" %e)

    if response['input_check'] != 'passed':
      raise InvalidInput(response['input_check'])
    
    if response['processing_status'] != 'success':
      raise ServiceError(response['processing_status'])

    return response['result']

  def __getattr__(self, attr):
    if 'endpoints' in self.__dict__ and attr not in self.__dict__['endpoints']:
      raise AttributeError(attr)
    self.__dict__['fname'] = attr
    return self

class RatereviewJSONClient(WrservicesJSONClient):
  def __init__(self, key = '', secret = ''):
    endpoints = {
      "getAverageRating": ["entities", "options"],
      "getTopEntities": ["entity_type", "options"],
      "getRatingsForEntity": ["entities", "options"],
      "getRatingsByUser": ["users", "options"],
      "setRating": ["entity", "userid", "rating"],
      "deleteRating": ["entity", "userid"],
      "getReviewCount": ["entities", "options"],
      "getReviewsForEntity": ["entities", "options"],
      "getReviewsByUser": ["users", "options"],
      "submitReview": ["in_review"],
      "deleteReview": ["entity", "userid"],
      "deleteReviewById": ["reviewid"],
      "getRatingDistribution": ["entities", "reviews_only", "locale"]
    }
    WrservicesJSONClient.__init__(self, service='ratereview', version='v1', api_key=key, secret=secret, endpoints = endpoints)
  
