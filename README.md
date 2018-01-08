# TRCTR-PLLR

TRCTR-PLLR generates random location data that reflects demographic data from the 2010 US Census. It's a faker. _Fake_ has become an overused and untrustworthy word based on data

https://www.census.gov/geo/maps-data/data/gazetteer2010.html

CREATE TABLE gaz_tracts (
    usps character varying(2),
    geoid character varying(11),
    pop10 integer,
    hu10 integer,
    aland bigint,
    awater bigint,
    aland_sqmi numeric,
    awater_sqmi numeric,
    intptlat numeric,
    intptlong numeric
);

Delete header row since it's a text file, not a csv file.
COPY gaz_tracts FROM '/Users/erictheise/Repos/erictheise/sample-from-census/data/Gaz_tracts_national.txt';

SELECT g.geoid, g.pop10, g.USPS
FROM gaz_tracts AS g
LEFT JOIN censustracts_example AS ce ON g.geoid = ce.geoid
WHERE g.pop10 > 0
ORDER BY g.pop10 DESC
;

returns 73426 rows

Use a windowing function. Pretty easy!
https://stackoverflow.com/questions/5698452/count-cumulative-total-in-postgresql/5700744#5700744
https://www.postgresql.org/docs/9.6/static/functions-window.html

SELECT i.geoid, i.pop10, i.cumulative-i.pop10 AS start, i.cumulative AS end
FROM (
  SELECT g.geoid, g.pop10, sum(g.pop10) OVER (ORDER BY g.geoid) AS cumulative
  FROM gaz_tracts AS g
  LEFT JOIN censustracts_example AS ce ON g.geoid = ce.geoid
  WHERE g.pop10 > 0
  ORDER BY g.geoid
) AS i
;

Use a RANGE type. [) is assumed so no need to adjust end by minus one.
https://www.postgresql.org/docs/9.6/static/rangetypes.html


SELECT i.*, CONCAT('[', i.cumulative-i.pop10, ',', i.cumulative, ')')::int8range
  FROM (
    SELECT g.geoid, sum(g.pop10) OVER (ORDER BY g.geoid) AS cumulative, g.pop10, g.usps
    FROM gaz_tracts AS g
    LEFT JOIN censustracts_example AS ce ON g.geoid = ce.geoid
    WHERE g.pop10 > 0
    ORDER BY g.geoid
  ) AS i
;

CREATE TABLE tract_distribution (
  geoid character varying(11),
  usps character varying(2),
  pop10 integer,
  cumulative bigint,
  weight int8range,
  wkb_geometry geometry(MultiPolygonZ,4269)
);

INSERT INTO tract_distribution
SELECT i.geoid, i.usps, i.pop10, i.cumulative, CONCAT('[', i.cumulative-i.pop10, ',', i.cumulative, ')')::int8range, i.wkb_geometry
FROM (
  SELECT g.geoid, sum(g.pop10) OVER (ORDER BY g.geoid) AS cumulative, g.pop10, g.usps, ce.wkb_geometry
  FROM gaz_tracts AS g
  LEFT JOIN censustracts_example AS ce ON g.geoid = ce.geoid
  WHERE g.pop10 > 0
  ORDER BY g.geoid
  ) AS i
; 

Add `bbox` field and UPDATE
```postgresql
UPDATE tract_distribution AS t
SET bbox=ST_SetSRID(s.bbox,4269)
FROM (
  SELECT geoid, ST_AsText(ST_Envelope(wkb_geometry)) AS bbox
  FROM tract_distribution
) AS s
WHERE t.geoid = s.geoid;
```

## Flask app

```
FLASK_APP=trctr_pllr.py FLASK_DEBUG=1 flask run
```
