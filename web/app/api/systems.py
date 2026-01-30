from flask import request
from . import api
from app.models import db, System
from flask import jsonify, session
from flask import current_app
from config import parse_systems_config
import os
import json

@api.route("/systems/update", methods=["POST"])
def update_system():
    
    data = request.get_json()
    server_systems = data["systems"]

    app_systems = db.session.query(System).all()
    for dbSystem in app_systems: # iterate over db-app systems to find removed or updated systems
        systemName = dbSystem.name

        if systemName not in current_app.config["SYSTEMS_CONFIG"]: # if a system is in db-app but not in SYSTEMS_CONFIG, add it to SYSTEMS_CONFIG
            current_app.config["SYSTEMS_CONFIG"][systemName] = {"type": 'ranking' if dbSystem.type == 'RANK' else 'recommender'}
        
        if systemName not in server_systems: # if system removed from server, remove it from db-app
            if systemName in current_app.config["SYSTEMS_CONFIG"] and current_app.config["SYSTEMS_CONFIG"][systemName].get("base", False):
                current_app.logger.error(f"Cannot delete baseline system: {systemName}")
                continue
            
            try:
                db.session.delete(dbSystem)
                db.session.commit()
                del current_app.config["SYSTEMS_CONFIG"][systemName]
                current_app.logger.info(f"System deleted: {systemName}")
            except Exception as e:
                current_app.logger.error(f"Error deleting system {systemName}: {str(e)}")
                db.session.rollback()
            continue
            
        systemStatus = server_systems[systemName].get("status", 'LIVE')
        if dbSystem.system_type != systemStatus: # if system status changed, update it
            if systemStatus == 'STOPPED' and systemName in current_app.config["SYSTEMS_CONFIG"] and current_app.config["SYSTEMS_CONFIG"][systemName].get("base", False):
                current_app.logger.error(f"Cannot stop baseline system: {systemName}")
            else:
                dbSystem.system_type = systemStatus
                db.session.commit()
                current_app.logger.info(f"System status updated: {systemName} - {systemStatus}")


    for systemName, sys_data in server_systems.items(): # iterate over server systems to find new systems
        systemType = sys_data.get("type", None)
        systemStatus = sys_data.get("status", None)

        dbSystem = db.session.query(System).filter_by(name=systemName).first()
        if dbSystem is None: # if new system from server, add it to app
            newSystem = System(
                name=systemName, 
                type=systemType, 
                system_type=systemStatus, 
                num_requests=0,
                num_requests_no_head=0
            )
            db.session.add(newSystem)
            db.session.commit()

            current_app.config["SYSTEMS_CONFIG"][systemName] = {"type": 'ranking' if systemType == 'RANK' else 'recommender'}

            current_app.logger.info(f"System added: {systemName}")
        

    # Update SYSTEMS_CONFIG related lists
    (
        current_app.config["RANKING_CONTAINER_NAMES"],
        current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"],
        current_app.config["RANKING_BASELINE_CONTAINER"],
        current_app.config["RECOMMENDER_CONTAINER_NAMES"],
        current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"],
        current_app.config["RECOMMENDER_BASELINE_CONTAINER"],
        _,
    ) = parse_systems_config(current_app.config["SYSTEMS_CONFIG"])

    return jsonify({"msg": f"Systems updated"}), 200