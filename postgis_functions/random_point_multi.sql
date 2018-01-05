-- Taken from https://trac.osgeo.org/postgis/wiki/UserWikiRandomPoint

CREATE OR REPLACE FUNCTION RandomPointMulti (
                geom Geometry
        )
        RETURNS Geometry
        AS $$
DECLARE
        maxiter INTEGER := 100000;
        i INTEGER := 0;
        n INTEGER := 0; -- total number of geometries in collection
        g INTEGER := 0; -- geometry number in collection to find random point in
        total_area DOUBLE PRECISION; -- total area
        cgeom Geometry;
BEGIN
        total_area = ST_Area(geom);
        n = ST_NumGeometries(geom);

        WHILE i < maxiter LOOP
                i = i + 1;
                g = floor(random() * n)::int;
                cgeom = ST_GeometryN(geom, g); -- weight the probability of selecting a subpolygon by its relative area
                IF random() < ST_Area(cgeom)/total_area THEN
                        RETURN RandomPoint( cgeom );
                END IF;
        END LOOP;

        RAISE EXCEPTION 'RandomPointMulti: too many iterations';
END;
$$ LANGUAGE plpgsql;
