# -*- coding: utf-8 -*-

def parse_query_string(p_where):
    pairs = p_where.split('|')
    params = []
    search_string = '1=1'
    for item, value in [cond.split('=') for cond in pairs]:
        import re

        if re.search('_like$', item):
            item = item.rsplit('_', 1)[0]
            search_string += " and upper(" + item + ") like %s"
            params.append(value.upper())
        elif re.search('_gt$', item):
            item = item.rsplit('_', 1)[0]
            if re.search('_DATE$', value):
                search_string += " and " + item + ">DATE %s"
                value = value.rsplit('_', 1)[0]
            else:
                search_string += " and " + item + ">%s" 
            params.append(value)
        elif re.search('_gte$'):
            item = item.rsplit('_', 1)[0]
            if re.search('_DATE$', value):
                search_string += " and " + item + ">=DATE %s"
                value = value.rsplit('_', 1)[0]
            else:
                search_string += " and " + item + ">=%s" 
            params.append(value)
        elif re.search('_lt$'):
            item = item.rsplit('_', 1)[0]
            if re.search('_DATE$', value):
                search_string += " and " + item + "<DATE %s"
                value = value.rsplit('_', 1)[0]
            else:
                search_string += " and " + item + "<%s" 
            params.append(value)
        elif re.search('_lte$'):
            item = item.split('_')[0]
            if re.search('_DATE$', value):
                search_string += " and " + item + "<=DATE %s"
                value = value.rsplit('_', 1)[0]
            else:
                search_string += " and " + item + "<=%s" 
            params.append(value)
        else: # equation
            search_string = " and " + item + "=%s"
            params.append(value)
  
        for i in range(len(params)):
            if params[i][:1] != '%':
                params[i] = '%' + params[i]
            if params[i][len(params[i]) - 1:] != '%':
                params[i] += '%'
  
        return search_string, params
            

def add_like(p_where, item, value):
    if item is None or value is None:
        return p_where
    if not p_where:
        p_where = 'p_where='
    p_where += item + '_like=' + value
    return p_where

def add_separator(p_where):
    p_where += '|'
    return p_where

#def add_and(p_where):
#    p_where += '&'
#    return p_where

def add_lte(p_where, item, value):
    return add_lt(p_where, item, value, equation=True)
    
def add_lt(p_where, item, value, equation=False):
    postfix = '_lt'
    if equation:
        postfix = '_lte'
    return add_eq(p_where, item + postfix, value)

def add_date_lt(p_where, item, value):
    return add_lt(p_where, item + '_DATE', value)

def add_date_lte():
    return add_lte(p_where, item + '_DATE', value)

def add_gte(p_where, item, value):
    return add_gt(p_where, item, value, equation=True)

def add_gt(p_where, item, value, equation=False):
    postfix = '_gt'
    if equation:
        postfix = '_gte'
    return add_eq(p_where, item + postfix, value)

def add_date_gt(p_where, item, value):
    return add_gt(p_where, item + '_DATE', value)

def add_date_gte():
    return add_gte(p_where, item + '_DATE', value)


def add_eq(p_where, item, value, is_fk=False, fk_postfix='_id'):
    if not p_where:
        p_where = 'p_where='
    if is_fk:
        p_where += item + fk_postfix + '=' + value
    else:
        p_where += item + '=' + value
    return p_where
