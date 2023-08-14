docker exec -it freeciv-web bash -c "sed -i '1241cvision_radius_sq = 8' /home/docker/freeciv/share/freeciv/classic/units.ruleset"
docker exec -it freeciv-web bash -c "sed -n -e "1241p" /home/docker/freeciv/share/freeciv/classic/units.ruleset"
docker exec -it freeciv-web bash -c "cd /docker/freeciv-web/; sh build.sh"
docker commit freeciv-web freeciv/freeciv-web
