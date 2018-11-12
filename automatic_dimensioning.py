# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AutomaticDimensioning
                                 A QGIS plugin
 This plugin caluclates the required cable capacities in a FTTH project
                              -------------------
        begin                : 2018-05-31
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Mohannad ADHAM / Axians
        email                : mohannad.adm@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import PyQt4
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import psycopg2
import psycopg2.extras
import xml.etree.ElementTree as ET
import xlrd
import xlwt
import os.path
import os
import subprocess
import osgeo.ogr  
import processing



from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from automatic_dimensioning_dialog import AutomaticDimensioningDialog
import os.path


class AutomaticDimensioning:
    global conn, cursor
    # global isMultistring
    isMultistring = False
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'AutomaticDimensioning_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&AutomaticDimensioning')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'AutomaticDimensioning')
        self.toolbar.setObjectName(u'AutomaticDimensioning')

        # Create the dialog (after translation) and keep reference
        self.dlg = AutomaticDimensioningDialog()

#"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""" Connect the buttons to the corresponding methods """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
        
        

        #creation du bouton "connexion BD"
        Button_connexion_BD= self.dlg.findChild(QPushButton,"pushButton_connexion")
        QObject.connect(Button_connexion_BD, SIGNAL("clicked()"),self.connectToDb)
        #mot de passe en etoile
        self.dlg.lineEdit_Password.setEchoMode(QLineEdit.Password)

        # Connect the button "pushButton_verifier_topologie"
        Button_verifier_topologie = self.dlg.findChild(QPushButton, "pushButton_verifier_topologie")
        QObject.connect(Button_verifier_topologie, SIGNAL("clicked()"), self.verify_topology)
        # Connect the button "pushButton_orientation"
        Button_orientation = self.dlg.findChild(QPushButton, "pushButton_orientation")
        QObject.connect(Button_orientation, SIGNAL("clicked()"), self.calcul_orientation)

        # Connect the button "pushButton_fibres_utiles"
        Button_fibres_utiles = self.dlg.findChild(QPushButton, "pushButton_fibres_utiles")
        QObject.connect(Button_fibres_utiles, SIGNAL("clicked()"), self.calcul_fibres_utiles)

        # Connect the button "pushButton_"
        Button_dimensions = self.dlg.findChild(QPushButton, "pushButton_dimensions")
        QObject.connect(Button_dimensions, SIGNAL("clicked()"), self.calcul_cable_dimensions)

        # Connect the butoon "pushButton_mettre_a_jour_chemin"
        Button_mettre_a_jour_chemin = self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_chemin")
        QObject.connect(Button_mettre_a_jour_chemin, SIGNAL("clicked()"), self.update_p_cheminement)

        # Connect the button "pushButton_mettre_a_jour_cable"
        Button_mettre_a_jour_cable = self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_cable")
        QObject.connect(Button_mettre_a_jour_cable, SIGNAL("clicked()"), self.update_p_cable)






#""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""        """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('AutomaticDimensioning', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
    

        # Create the dialog (after translation) and keep reference
        # self.dlg = AutomaticDimensioningDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/AutomaticDimensioning/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Performs Cable Dimensioning'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Automatic Dimensioning'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""

        self.GetParamBD(self.dlg.lineEdit_BD, self.dlg.lineEdit_Password, self.dlg.lineEdit_User, self.dlg.lineEdit_Host, self.dlg.Schema_grace)
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        # Activate the connection button 
        self.dlg.findChild(QPushButton, "pushButton_connexion").setEnabled(True)
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass




    def fenetreMessage(self,typeMessage,titre,message):
        ''' Displays a message box to the user '''

        try:
            msg = QMessageBox()
            # msg.setIcon(typeMessage)
            msg.setWindowTitle(titre)
            msg.setText(str(message))
            msg.setWindowFlags(PyQt4.QtCore.Qt.WindowStaysOnTopHint)
            msg.exec_()
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage",str(e))

            
    def GetParamBD(self, dbname, password, user, serveur, sche):
        ''' Looks for the information to connect to the DB within the QGIS project '''

        try:
            path_absolute = QgsProject.instance().fileName()
            
            if path_absolute != "":
                
                
                tree = ET.parse(path_absolute)
                sche.setText("gracethd")
                root = tree.getroot()

                listeModify = []
                
                for source in root.iter('datasource'):
                    
                    if "dbname" in source.text : 
                        modify = str(source.text)
                        listeModify = modify.split("sslmode")
                        if len(listeModify) > 1:
                            
                            break

                if len(listeModify) > 1 :
                    
                    infosConnexion = listeModify[0].replace("'","")
                    infosConnexion = infosConnexion.split(" ")
                    for info in infosConnexion:
                        inf = info.split("=")
                        if inf[0] == "dbname":
                            dbname.setText(inf[1])
                        if inf[0] == "password":
                            password.setText(inf[1])
                        if inf[0] == "user":
                            user.setText(inf[1])
                        if inf[0] == "host":
                            serveur.setText(inf[1])
                    schemainfo = listeModify[1].replace("'","")
                    schemainfo = schemainfo.split(" ")
                    for sch in schemainfo:
                        sh = sch.split("=")
                        if sh[0] == "table":
                            schema = sh[1].split(".")
                            # sche.setText(schema[0].replace('"',''))
                            sche.setText("gracethd")
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_GetParamBD",str(e))
            # print str(e)


    def remplir_menu_deroulant_reference(self, combobox, rq_sql, DefValChamp):
        ''' Fill a combobox with a list of table names '''

        listVal = []
        combobox.clear()
        result = self.executerRequette(rq_sql, True)
        for elm in result:
            listVal.append(elm[0])
        combobox.addItems(listVal)
        try:
            combobox.setCurrentIndex(combobox.findText(DefValChamp))
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_remplir_menu_deroulant_reference",str(e))




    def executerRequette(self, Requette, boool):
        ''' Sends a query to execute it within the database and receives the results '''

        global conn        
        try:
            cursor = conn.cursor()
            cursor.execute(Requette)
            conn.commit()
            if boool:
                result = cursor.fetchall()
                cursor.close()
                try :
                    if len(result)>0:
                        return result
                except:
                    return None
            else:
                cursor.close()
            
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_executerRequette",str(e))
            cursor.close()
            self.connectToDb()

            if "MultiLineString" in str(e):
                # self.fenetreMessage(QMessageBox, "info", "You have a cable with MultilineString geometry (cable id = " + str(self.findMultiLineString()) + ")")
                self.isMultistring = True
                self.findMultiLineString()


    def findMultiLineString(self):
        ''' Finds the features that have a multilinstring geometry type and add them as a layer within the project '''

        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()

        query = "SELECT id FROM temp.cable_" + zs_refpm.split("_")[2].lower()  + " WHERE ST_GeometryType(ST_LineMerge(geom)) = 'ST_MultiLineString'"
        result = self.executerRequette(query,  True)
        # return result[0][0]
        if len(result) > 0:
            message2 = "You have " + str(len(result)) + "  cables with MultilineString geometry at id = " + str(result[0][0])
            for i in range(1, len(result)):
                if i < len(result) - 1:
                    message2 += ", " + str(result[i][0])
                else :
                    message2 += " and " + str(result[i][0])
        message2 += "\n Please consult the table cable_multilinestring_" + zs_refpm.split("_")[2].lower()
        self.fenetreMessage(QMessageBox, "Warning!", message2)

        query2 = """ DROP TABLE IF EXISTS temp.cable_multilinestring_""" + zs_refpm.split("_")[2].lower()  + """;

                CREATE TABLE temp.cable_multilinestring_""" + zs_refpm.split("_")[2].lower()  + """ AS 
                SELECT id, geom FROM temp.cable_""" + zs_refpm.split("_")[2].lower()  + """ WHERE ST_GeometryType(geom) = 'ST_MultiLineString';

         """
        self.executerRequette(query2,  False)
        self.add_pg_layer("temp", "cable_multilinestring_" + zs_refpm.split("_")[2].lower())




    def connectToDb(self):
        ''' Connects to the DB, enables the comboboxes and the buttons, and fill the comboboxes with the names of the tables '''
        global conn
        Host = self.dlg.lineEdit_Host.text()
        DBname = self.dlg.lineEdit_BD.text()
        User = self.dlg.lineEdit_User.text()
        Password = self.dlg.lineEdit_Password.text()
        Schema = self.dlg.Schema_grace.text()
        Schema_prod = self.dlg.Schema_prod.text()

        
        conn_string = "host='"+Host+"' dbname='"+DBname+"' user='"+User+"' password='"+Password+"'"

        try:
            conn = psycopg2.connect(conn_string)
            #recuperer tout les schemas
            shema_list=[]
            cursor = conn.cursor()
            sql =  "select schema_name from information_schema.schemata "
            cursor.execute(sql)
            result=cursor.fetchall()
            for elm in result:
                shema_list.append(elm[0].encode("utf8"))
            #passer au deuxieme onglet si la connexion est etablit et si le schema existe
            if Schema in shema_list:
                # Do Something
                # Enable the Comboboxes and Buttons

                self.dlg.findChild(QComboBox,"comboBox_suf").setEnabled(True)
                self.dlg.findChild(QComboBox,"comboBox_cheminement").setEnabled(True)
                self.dlg.findChild(QComboBox,"comboBox_noeud").setEnabled(True)
                self.dlg.findChild(QComboBox, "comboBox_ebp").setEnabled(True)
                self.dlg.findChild(QComboBox, "comboBox_sitetech").setEnabled(True)
                self.dlg.findChild(QComboBox, "comboBox_zs_refpm").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_verifier_topologie").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_orientation").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_fibres_utiles").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_dimensions").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_chemin").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_cable").setEnabled(True)

                # self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_chemin")
                # self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_cable").setEnabled(True)
                # Disable connection button
                self.dlg.findChild(QPushButton, "pushButton_connexion").setEnabled(False)

                # Search for the names of the required tables in each schema
                # 1 - in gracethd
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_suf, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_grace.text()+"' ;"), 't_suf')
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_noeud, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_grace.text()+"' ;"), 't_noeud')
                
                # 2 - in prod
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_cheminement, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_prod.text()+"' ;"), 'p_cheminement')
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_ebp, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_prod.text()+"' ;"), 'p_ebp')
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_sitetech, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_prod.text()+"' ;"), 'p_sitetech') 
                # self.fenetreMessage(QMessageBox.Warning,"Query for zs_refpm", "SELECT zs_refpm FROM " + self.dlg.Schema_grace.text() + ".t_zsro;")
                # result = self.executerRequette("SELECT zs_refpm FROM " + self.dlg.Schema_grace.text() + ".t_zsro;", True)
                # for elm in result:
                #     print elm[0]
                #     self.fenetreMessage(QMessageBox.Warning,"result of query", elm[0])

                # 3 - ZSRO (zs_refpm)
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_zs_refpm, ("SELECT zs_refpm as refpm FROM " + self.dlg.Schema_prod.text() + ".p_zsro ;"), 'PMT_26325_FO01')


                print "Schema found"
            else:
                # self.dlg2.findChild(QPushButton,"pushButton_controle_avt_migration").setEnabled(False)
                print "Schema not found"
        except Exception as e:
                pass
            #desactiver les bouton
            # self.dlg2.findChild(QPushButton,"pushButton_controle_avt_migration").setEnabled(False)
            # self.dlg2.findChild(QPushButton,"pushButton_migration").setEnabled(False)
            #         self.fenetreMessage(QMessageBox.Warning,"Erreur_connectToDb",str(e))
            #         cursor.close()


    def calcul_orientation(self):
        ''' Determines the orientation of the cheminements within the the temporary table, adds the resulted table
        as a layer to the project and styles it '''

        message =  "calcu_orientation function"
        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()
        self.fenetreMessage(QMessageBox, "Successful!", message)
        # Create temp cheminement table
        # table_name = self.dlg.comboBox_cheminement.text()
        table_name = "p_cheminement"
        # self.fenetreMessage(QMessageBox, "Successful!", table_name)
        schema_name = self.dlg.Schema_prod.text()
        # self.fenetreMessage(QMessageBox, "Successful!", schema_name)
        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()
        # self.fenetreMessage(QMessageBox, "Successful!", zs_refpm)

        self.create_temp_table(schema_name, table_name, zs_refpm)

        # The SQL query for determining the orientation of conduites



        query3 = """DO
                $$
                DECLARE
                counter integer = 1 ;
                rang_fibre integer;
                id record ;
                id2 record ;

                BEGIN

                    DROP TABLE IF EXISTS temp.clusters;
                    CREATE TABLE temp.clusters (gid serial, this_id integer, rang integer, geom Geometry(Linestring,2154));
                    DROP TABLE IF EXISTS temp.clusters2;
                    CREATE TABLE temp.clusters2 (gid serial, that_id integer);
                    DROP TABLE IF EXISTS temp.clusters3;
                    CREATE TABLE temp.clusters3 (gid serial, that_id integer);   
                    CREATE INDEX clusters_geom_gist ON temp.clusters USING GIST (geom);  
                    INSERT INTO temp.clusters(this_id, rang, geom)   
                    SELECT c.cm_id, counter, c.geom
                    FROM prod.p_cheminement c, prod.p_sitetech s 
                    WHERE ST_INTERSECTS(c.geom, s.geom) AND st_id = (SELECT lt_st_code FROM prod.p_ltech WHERE lt_etiquet LIKE '%""" + zs_refpm.split("_")[2] + """');

                    FOR id IN (SELECT cm_id FROM prod.p_cheminement WHERE cm_zs_code LIKE '%""" + zs_refpm.split("_")[2] + """%' 
                    AND cm_typelog IN ('RA','DI','TD'))

                    LOOP
                    
                    counter = counter + 1;
                    
                    INSERT INTO temp.clusters(this_id, rang, geom)
                    SELECT c.cm_id, counter, c.geom
                    FROM prod.p_cheminement c, temp.clusters l
                    WHERE l.rang = (counter - 1) AND (St_DWITHIN(St_StartPoint(c.geom), St_StartPoint(l.geom),0.0001) 
                    OR St_DWITHIN(St_StartPoint(c.geom), St_Endpoint(l.geom),0.0001) 
                    OR St_DWITHIN(St_EndPoint(c.geom), St_StartPoint(l.geom),0.0001) 
                    OR St_DWITHIN(St_EndPoint(c.geom), St_EndPoint(l.geom),0.0001)) AND cm_typelog IN ('RA','DI','TD') 
                    AND c.cm_id NOT IN (SELECT this_id FROM temp.clusters) AND c.cm_zs_code LIKE '%""" + zs_refpm.split("_")[2] + """%';
                       
                    
                    END LOOP;

                    DELETE FROM temp.clusters WHERE gid IN (
                                    SELECT gid--, this_id, quantite
                                    FROM (
                                        SELECT gid, this_id, ROW_NUMBER() OVER(PARTITION BY this_id ORDER BY this_id) as quantite
                                        FROM temp.clusters
                                        WHERE this_id IN (SELECT this_id FROM temp.clusters GROUP BY this_id HAVING count(this_id) > 1)
                                        ) AS A 
                                    WHERE quantite > 1
                                    ORDER BY this_id
                                    );


                For id in (Select * from temp.clusters order by gid) loop
                For id2 in (select * from temp.clusters where (St_DWITHIN(St_StartPoint(id.geom), St_StartPoint(geom),0.0001) 
                OR St_DWITHIN(St_StartPoint(id.geom), St_Endpoint(geom),0.0001) 
                OR St_DWITHIN(St_EndPoint(id.geom), St_StartPoint(geom),0.0001) 
                OR St_DWITHIN(St_EndPoint(id.geom), St_EndPoint(geom),0.0001)) 
                and id.rang = (rang - 1)) loop
                If St_Dwithin((Select St_EndPoint(geom) from temp.clusters where gid = id.gid),
                (Select St_EndPoint(geom) from temp.clusters where gid = id2.gid),0.0001) IS TRUE then  
                --RAISE EXCEPTION USING MESSAGE = (id,id2);
                --IF id2.this_id IN (Select that_id from temp.clusters2) then RAISE EXCEPTION USING MESSAGE = (that_id); End If;
                --RAISE EXCEPTION USING MESSAGE = (id,id2);

                IF id2.this_id IN (Select that_id from temp.clusters2) then 
                INSERT INTO temp.clusters3 (that_id) VALUES (id2.this_id);
                End If;
                INSERT INTO temp.clusters2 (that_id) VALUES (id2.this_id);
                UPDATE temp.clusters SET geom = ST_Reverse(geom) where this_id = id2.this_id;
                End If;
                End loop;
                End loop;

                        
                UPDATE temp.cheminement_""" + zs_refpm.split("_")[2] + """
                    SET geom = A.geom
                    FROM (
                        SELECT this_id, geom
                        FROM temp.clusters
                         ) as A
                    WHERE temp.cheminement_""" + zs_refpm.split("_")[2] + """.cm_id = a.this_id;

                DELETE FROM temp.clusters WHERE gid IN (
                                    SELECT gid--, this_id, quantite
                                    FROM (
                                        SELECT gid, this_id, ROW_NUMBER() OVER(PARTITION BY this_id ORDER BY this_id) as quantite
                                        FROM temp.clusters
                                        WHERE this_id IN (SELECT this_id FROM temp.clusters GROUP BY this_id HAVING count(this_id) > 1)
                                        ) AS A 
                                    WHERE quantite > 1
                                    ORDER BY this_id
                                    );

                                    
                END;
                $$ language plpgsql;

                -- The remaining records within clusters3 are loops in the infrastructure
                Select * from temp.clusters3;


        """
        ############################## Important: pay attention to the number of sitetech (st_id). We should get it dynamically from the table p_ltech ###############
        ########################### We should also check the connectivity between the cheminements and the sitetech ##################################################
        ########################### Other possibility: The first cheminement after the site technique has fauty direction ############################################
        ########################## Other possibility: There are cheminement assigned an incorrect values of zs_code ##################################################

        # Execute the query that determines the orientation of the cables
        result = self.executerRequette(query3, True)

        # Add the layer to the project
        self.add_pg_layer("temp", "cheminement_" + zs_refpm.split("_")[2].lower())

        # Copy the style of the layer "cheminement" to the newly added layer
        self.copy_style("p_cheminement", "cheminement_" + zs_refpm.split("_")[2].lower())

        # Check for loops in the infrastructure
        if len(result) > 0:
                message2 = "You have " + str(len(result)) + " loops in your network at cheminements " + str(result[0][1])
                for i in range(1, len(result)):
                    if i < len(result) - 1:
                        message2 += ", " + str(result[i][1])
                    else :
                        message2 += " and " + str(result[i][1])


        else:
            self.fenetreMessage(QMessageBox, "Successful!" ,"The table is oriented")

        


    def calcul_fibres_utiles(self):
        ''' Calculates the number of fibers per cheminement within the working table cheminement_* '''

        message = "calcul_fibres_utiles function"
        self.fenetreMessage(QMessageBox, "info" , message)
        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()
        # zs_refpm = self.dlg.comboBox_zs_refpm.currentText()


        query2 = """
                DO
                $$
                DECLARE
                counter integer = 1 ;
                rang_fibre integer;
                id record ;
                id2 record ;
                sro text ;
                base text;

                BEGIN


                sro = '""" + zs_refpm.split("_")[2] + """'; ---entrez le SRO


                EXECUTE 'DROP TABLE IF EXISTS temp.p_cheminement_' || sro;
                EXECUTE 'CREATE TABLE temp.p_cheminement_' || sro || '(gid serial, rang integer, this_id integer, fo_util integer, reserve integer, geom Geometry(Linestring,2154))';
                ALTER TABLE temp.p_cheminement_""" + zs_refpm.split("_")[2] + """ ADD PRIMARY KEY (gid);
                CREATE INDEX ON temp.p_cheminement_""" + zs_refpm.split("_")[2] + """ USING GIST(geom); 
                EXECUTE 'INSERT INTO temp.p_cheminement_' || sro || '(this_id, rang, geom) SELECT this_id, rang, geom from temp.clusters';

                --------------------------------------------------------------------------------------

                EXECUTE ' UPDATE temp.p_cheminement_' || sro || '
                     SET fo_util = B.total_fibr,
                     reserve = B.total_fibr * 2 ------ new 1 ------
                     FROM (
                        SELECT c.cm_id as this_id, n.total_fibr 
                        FROM temp.cheminement_""" +  zs_refpm.split("_")[2] + """ c 
                        LEFT JOIN (
                                   SELECT n.nd_code, vs.total_fibr, n.geom 
                                   FROM gracethd.t_noeud n, prod.vs_bal vs 
                                   WHERE n.nd_code = vs.nd_code AND n.nd_r1_code =''SADN'' --AND vs.total_suf BETWEEN 1 AND 3
                                   ) as n
                        ON ST_DWithin(St_EndPoint(c.geom), n.geom, 0.0001)
                        WHERE c.cm_zs_code LIKE ''%'|| sro ||'%'' AND n.total_fibr IS NOT NULL 
                         ) AS B
                     WHERE temp.p_cheminement_' || sro || '.this_id = B.this_id';


                -------------------------------- New part developped by Kevin ---------------------------


                /*EXECUTE ' UPDATE temp.p_cheminement_' || sro || '
                        SET fo_util = A.zd_fo_util,
                            reserve = A.reserve  --------- new 2 --------

                        FROM (
                            SELECT f.this_id, zd_fo_util, 
                            (SUM(f2.reserve) + (Case when z.zd_fo_util IS NOT NULL then z.zd_fo_util else 0 End)) as reserve ------------------- new 3 -----------------------
                            FROM temp.p_cheminement_' || sro || ' f
                            LEFT JOIN temp.p_cheminement_' || sro || ' f2 ON ST_DWITHIN(ST_EndPoint(f.geom), ST_StartPoint(f2.geom), 0.0001)
                            LEFT JOIN prod.p_ebp e ON ST_DWITHIN(ST_EndPoint(f.geom), e.geom, 0.0001)
                            LEFT JOIN prod.p_zdep z ON e.bp_id = z.zd_r6_code
                            WHERE f2.this_id IS NULL AND e.bp_id IS NOT NULL AND e.bp_pttype <> 7
                            GROUP BY f.this_id, f.rang, z.zd_fo_util
                            ORDER BY f.this_id
                            ) AS A
                        WHERE temp.p_cheminement_' || sro || '.this_id = A.this_id';*/


                --------------------------------------------------------------------------------------------


                DROP TABLE IF EXISTS temp.p_cheminement_tbr;
                CREATE TABLE temp.p_cheminement_tbr (gid serial, rang integer, this_id integer, fo_util integer, reserve integer, geom Geometry(Linestring,2154));
                EXECUTE 'INSERT INTO temp.p_cheminement_tbr SELECT * FROM temp.p_cheminement_' || sro; 

                    For id in (Select gid from temp.p_cheminement_tbr WHERE fo_util IS NULL order by rang DESC) loop
                    
                     EXECUTE 'UPDATE temp.p_cheminement_' || sro || ' c SET fo_util = (Select (SUM(c2.fo_util) + (Case when (Select SUM(z.zd_fo_util)
                     FROM prod.p_ebp e LEFT JOIN prod.p_zdep z ON e.bp_id = zd_r6_code WHERE ST_Dwithin(e.geom,St_EndPoint(c.geom),0.0001) ) IS NOT NULL 
                     THEN (Select SUM(z.zd_fo_util) from prod.p_ebp e LEFT JOIN prod.p_zdep z ON e.bp_id = zd_r6_code WHERE ST_Dwithin(e.geom,St_EndPoint(c.geom),0.0001) ) else 0 End )) As fo_util 
                     FROM temp.p_cheminement_' || sro || ' c2 WHERE ST_Dwithin(St_StartPoint(c2.geom),St_EndPoint(c.geom),0.0001)),
                     reserve = (Select (SUM(c2.reserve) + (Case when (Select SUM(z.zd_fo_util)
                     FROM prod.p_ebp e LEFT JOIN prod.p_zdep z ON e.bp_id = zd_r6_code WHERE ST_Dwithin(e.geom,St_EndPoint(c.geom),0.0001) ) IS NOT NULL 
                     THEN (Select SUM(z.zd_fo_util) from prod.p_ebp e LEFT JOIN prod.p_zdep z ON e.bp_id = zd_r6_code WHERE ST_Dwithin(e.geom,St_EndPoint(c.geom),0.0001) ) else 0 End )) As fo_util 
                     FROM temp.p_cheminement_' || sro || ' c2 WHERE ST_Dwithin(St_StartPoint(c2.geom),St_EndPoint(c.geom),0.0001))

                     WHERE c.gid = $1' USING id.gid;
                     --EXECUTE 'UPDATE temp.p_cheminement_' || sro || ' c SET fo_util = (Select (SUM(c2.fo_util) + (Case when z.zd_fo_util IS NOT NULL then z.zd_fo_util else 0 End)) As fo_util FROM temp.p_cheminement_' || sro || ' c2 LEFT JOIN prod.p_ebp e ON ST_Dwithin(e.geom,St_EndPoint(c.geom),0.0001) LEFT JOIN prod.p_zdep z ON e.bp_id = zd_r6_code WHERE ST_Dwithin(St_StartPoint(c2.geom),St_EndPoint(c.geom),0.0001) GROUP BY z.zd_fo_util) WHERE c.gid = $1' USING id.gid;
                    END LOOP;


                --------------------------------------------------------------------------------------


                EXECUTE 'UPDATE temp.cheminement_' || sro || ' SET cm_fo_util = temp_chemin.reserve FROM temp.p_cheminement_' || sro || ' AS temp_chemin WHERE cm_id = temp_chEmin.this_id';
                    
                DROP TABLE IF EXISTS temp.p_cheminement_tbr;
                                        
                END;
                $$ language plpgsql;

                """





        self.executerRequette(query2, False)


        # Enable the button of cable dimensioning
        self.dlg.findChild(QPushButton, "pushButton_dimensions").setEnabled(True)


    # ---------------------------------- needs to be modified --------------------------------------

    def create_temp_table(self, shema, table_name, zs_refpm):
        ''' Creates a working table for the cheminments filtered by zs_refpm. The method is implemented for cheminment_* 
        but we can generalize the body of the method to create any working table. '''

        # drop previous version if exists
        query_drop = "DROP TABLE IF EXISTS temp.Cheminement_" + zs_refpm.split("_")[2] + " CASCADE;"
        # self.fenetreMessage(QMessageBox, "Drop!", query_drop)
        self.executerRequette(query_drop, False)
        # temporarry Cheminement table
        # query_inner = "SELECT * FROM temp.p_cheminement WHERE cm_zs_code like '%" + zs_refpm.split("_")[2] + "%' AND cm_typelog IN ('TD', 'DI', 'RA')"
        query_inner = "SELECT * FROM prod.p_cheminement WHERE cm_zs_code like '%" + zs_refpm.split("_")[2] + "%'"
        query_outer = """CREATE TABLE temp.Cheminement_""" + zs_refpm.split("_")[2] + """ as (""" + query_inner + """);
         ALTER TABLE temp.Cheminement_""" + zs_refpm.split("_")[2] + """ ADD PRIMARY KEY (cm_id);
         CREATE INDEX ON temp.Cheminement_""" + zs_refpm.split("_")[2] + """ USING GIST(geom); 
         """
        # self.fenetreMessage(QMessageBox, "Successful!", query_outer)
        self.executerRequette(query_outer, False)

    #------------------------------------------------------------------------------------------------


    def verify_topology(self):
        ''' Check the connectivity between all the cheminements within the zsro.
        Adds a table to the project that should have only one record in case of success '''

        # zs_refpm = self.dlg.comboBox_zs_refpm.currentText()
        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()

        # self.fenetreMessage(QMessageBox, "Success", "Topology will be verified")

        query_topo_new = """DO
                        $$
                        DECLARE
                        this_id bigint;
                        this_geom geometry;
                        cluster_id_match integer;

                        id_a bigint;
                        id_b bigint;

                        BEGIN
                        DROP TABLE IF EXISTS temp.cm_continuite_""" + zs_refpm.split("_")[2].lower().lower() + """;
                        CREATE TABLE temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ (cluster_id serial, ids bigint[], geom geometry);
                        CREATE INDEX ON temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ USING GIST(geom);

                        -- Iterate through linestrings, assigning each to a cluster (if there is an intersection)
                        -- or creating a new cluster (if there is not)
                        -- We limit the query to only the concerning ZSRO
                        FOR this_id, this_geom IN (SELECT cm_id, geom FROM prod.p_cheminement WHERE cm_zs_code like '%""" + zs_refpm.split("_")[2].lower() + """%') LOOP
                          -- Look for an intersecting cluster.  (There may be more than one.)
                          SELECT cluster_id FROM temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ WHERE ST_Intersects(this_geom, temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """.geom)
                             LIMIT 1 INTO cluster_id_match;

                          IF cluster_id_match IS NULL THEN
                             -- Create a new cluster
                             INSERT INTO temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ (ids, geom) VALUES (ARRAY[this_id], this_geom);
                          ELSE
                             -- Append line to existing cluster
                             UPDATE temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ SET geom = ST_Union(this_geom, geom),
                                                  ids = array_prepend(this_id, ids)
                             WHERE temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """.cluster_id = cluster_id_match;
                          END IF;
                        END LOOP;

                        -- Iterate through the temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """, combining temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ that intersect each other
                        LOOP
                            SELECT a.cluster_id, b.cluster_id FROM temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ a, temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ b 
                             WHERE ST_Intersects(a.geom, b.geom)
                               AND a.cluster_id < b.cluster_id
                              INTO id_a, id_b;

                            EXIT WHEN id_a IS NULL;
                            -- Merge cluster A into cluster B
                            UPDATE temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ a SET geom = ST_Union(a.geom, b.geom), ids = array_cat(a.ids, b.ids)
                              FROM temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ b
                             WHERE a.cluster_id = id_a AND b.cluster_id = id_b;

                            -- Remove cluster B
                            DELETE FROM temp.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ WHERE cluster_id = id_b;
                        END LOOP;
                        END;
                        $$ language plpgsql;"""


        self.executerRequette(query_topo, False)
        self.fenetreMessage(QMessageBox, "Success", "Topology has been verified")
        try:
            self.add_pg_layer("temp", "cm_continuite_" + zs_refpm.split("_")[2].lower())
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage", str(e))
            # self.fenetreMessage(QMessageBox, "Success", "The topology verification layer wasn't added to the map")
        # self.fenetreMessage(QMessageBox, "Success", "The topology verification layer is added to the map")


    def add_pg_layer(self, schema, table_name):
        ''' Adds a postgres geometry table as a layer to the QGIS project.'''

        # Create a data source URI
        uri = QgsDataSourceURI()

        # set host name, port, database name, username and password
        uri.setConnection(self.dlg.lineEdit_Host.text(), "5432", self.dlg.lineEdit_BD.text(), self.dlg.lineEdit_User.text(), self.dlg.lineEdit_Password.text())

        # set database schema, table name, geometry column and optionally subset (WHERE clause)
        # uri.setDataSource('temp', 'cheminement_al01', "geom")
        uri.setDataSource(schema, table_name, "geom")

        vlayer = QgsVectorLayer(uri.uri(False), table_name, "postgres")

        # if not vlayer.isValid():
        #     self.fenetreMessage(QMessageBox, "Error", "The layer %s is not valid" % vlayer.name())
        #     return


        # check first if the layer is already added to the map
        layer_names = [layer.name() for layer in QgsMapLayerRegistry.instance().mapLayers().values()]
        if table_name not in layer_names:
            # Add the vector layer to the map
            QgsMapLayerRegistry.instance().addMapLayers([vlayer])
            self.fenetreMessage(QMessageBox, "Success", "Layer %s is loaded" % vlayer.name())

        else :
            self.fenetreMessage(QMessageBox, "Success", "Layer %s already exists but it has been updated" % vlayer.name())



    def remove_raccord(self, zs_refpm):
        ''' Removes the cheminements of type "Raccordement" from the working table cheminement_* 
        and saves the result in a new working table. '''

        query_remove = """
                        DO
                        $$
                        DECLARE
                        counter integer = 1;

                        Begin
                        DROP TABLE IF EXISTS temp.cheminement_""" + zs_refpm.split("_")[2].lower() + """_without_r;

                        CREATE TABLE temp.cheminement_""" + zs_refpm.split("_")[2].lower() + """_without_r AS 
                        (SELECT * FROM temp.cheminement_""" + zs_refpm.split("_")[2] + """);
                        ALTER TABLE temp.Cheminement_""" + zs_refpm.split("_")[2].lower() + """_without_r ADD PRIMARY KEY (cm_id);
                        CREATE INDEX ON temp.Cheminement_""" + zs_refpm.split("_")[2].lower() + """_without_r USING GIST(geom); 

                        LOOP

                        IF (SELECT count(*) FROM (SELECT A.cm_id, A.cm_comment, A.geom FROM 
                        temp.cheminement_""" + zs_refpm.split("_")[2].lower() + """_without_r AS A 
                            LEFT JOIN temp.cheminement_""" + zs_refpm.split("_")[2].lower() + """_without_r AS B 
                            ON ST_DWithin(ST_EndPoint(A.geom), ST_StartPoint(B.geom), 0.0001)
                            LEFT JOIN prod.p_ebp AS C
                            ON ST_DWithin(ST_EndPoint(A.geom), C.geom, 0.0001)
                            WHERE B.cm_id is null and C.bp_id is null) AS q) = 0 THEN 

                            EXIT;

                        END IF;

                        DELETE FROM temp.cheminement_""" + zs_refpm.split("_")[2].lower() + """_without_r WHERE cm_id IN 
                            (SELECT A.cm_id FROM temp.cheminement_""" + zs_refpm.split("_")[2].lower() + """_without_r AS A 
                                LEFT JOIN temp.cheminement_""" + zs_refpm.split("_")[2].lower() + """_without_r AS B 
                                ON ST_DWithin(ST_EndPoint(A.geom), ST_StartPoint(B.geom), 0.0001)
                                LEFT JOIN prod.p_ebp AS C
                                ON ST_DWithin(ST_EndPoint(A.geom), C.geom, 0.0001)
                                WHERE B.cm_id is null and C.bp_id is null);

                        counter = counter + 1;

                        END LOOP;

                        END;

                        $$ language plpgsql;"""

        self.executerRequette(query_remove, False)




    def create_cable_geom(self, schema, table_name, zs_refpm):
        ''' Create a new working table that holds the geometry of the cables which results from fusioning the cheminements between each two boites. '''

        query_drop = "DROP TABLE IF EXISTS " + schema + "." + table_name + "_" + zs_refpm.split("_")[2] + ";"
        # self.fenetreMessage(QMessageBox, "Drop!", query_drop)
        self.executerRequette(query_drop, False)

        create_geom = """DO
                    $$
                    BEGIN
                    ALTER TABLE temp.cheminement_""" + zs_refpm.split("_")[2] + """_without_r add column cable text;

                    UPDATE temp.cheminement_""" + zs_refpm.split("_")[2] + """_without_r SET cable = boite.bp_id 
                    FROM prod.p_ebp as boite WHERE ST_DWithin(ST_EndPoint(temp.cheminement_""" + zs_refpm.split("_")[2] + """_without_r.geom),
                     boite.geom, 0.0001);

                    LOOP

                    UPDATE temp.cheminement_""" + zs_refpm.split("_")[2] + """_without_r as cm1 SET cable = cm2.cable 
                    FROM temp.cheminement_""" + zs_refpm.split("_")[2] + """_without_r as cm2 
                    WHERE ST_DWithin(ST_EndPoint(cm1.geom), ST_StartPoint(cm2.geom), 0.0001) and cm1.cable is null and cm2.cable is not null;

                        IF (SELECT count(*) FROM temp.cheminement_""" + zs_refpm.split("_")[2] + """_without_r WHERE cable is null) = 0 THEN  
                            EXIT;  
                        END IF;
                    END LOOP;

                    CREATE TABLE temp.""" + table_name + """_""" + zs_refpm.split("_")[2] +""" AS (SELECT ROW_NUMBER() OVER() AS ID, GEOM 
                    FROM (SELECT cable,
                               ST_LineMerge(ST_Union(c.geom)) as geom
                             FROM temp.cheminement_""" + zs_refpm.split("_")[2] + """_without_r As c
                        GROUP BY cable)as cable_geom);


                    ALTER TABLE temp.cable_""" + zs_refpm.split("_")[2].lower() + """ ADD PRIMARY KEY (id);
                    CREATE INDEX ON temp.cable_""" + zs_refpm.split("_")[2].lower() + """ USING GIST(geom);

                    END;
                    $$
                    language plpgsql;

                    """
        # self.fenetreMessage(QMessageBox, "create cable geometry", create_geom)
        self.executerRequette(create_geom, False)




    def create_temp_cable_table(self, schema, table_name, zs_refpm):


        self.remove_raccord(zs_refpm)
        # self.fenetreMessage(QMessageBox, "info", "After remove raccord")
        try:
            self.add_pg_layer("temp", "cheminement_" + zs_refpm.split("_")[2].lower() + "_without_r")
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage", str(e))

        try:
            self.create_cable_geom(schema, table_name, zs_refpm)
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning, "Erreur_fenetreMessage", str(e))





    def fibre_utile_to_cable_capacity(self, zs_refpm):
        query = """UPDATE temp.cable_""" + zs_refpm.split("_")[2] + """ as cable
                SET capacite = subquery.case
                FROM
                (select id, fb_utile, CASE
                            WHEN fb_utile  <= 12 THEN 12 
                            WHEN fb_utile  > 12 AND fb_utile  <= 24 THEN 24
                            -- WHEN fb_utile > 24 AND fb_utile <= 36 THEN 36
                            -- WHEN fb_utile > 36 AND fb_utile <= 48 THEN 48
                            WHEN fb_utile  > 24 AND fb_utile  <= 48 THEN 48
                            WHEN fb_utile  > 48 AND fb_utile  <= 72 THEN 72
                            WHEN fb_utile  > 72 AND fb_utile  <= 96 THEN 96
                            WHEN fb_utile  > 96 AND fb_utile  <= 144 THEN 144
                            WHEN fb_utile  > 144 AND fb_utile  <= 288 THEN 288
                            WHEN fb_utile  > 288 AND fb_utile  <= 432 THEN 432
                            WHEN fb_utile  > 432 AND fb_utile  <= 576 THEN 576
                            WHEN fb_utile  > 576 AND fb_utile  <= 720 THEN 720
                            WHEN fb_utile  > 720 AND fb_utile  <= 864 THEN 864
                            
                            
                             END
                             FROM temp.cable_""" + zs_refpm.split("_")[2] + """) as subquery
                WHERE cable.id = subquery.id"""

        # self.fenetreMessage(QMessageBox, "Successful!", query)
        self.executerRequette(query, False)





    # def calcul_fb_utiles_cable(self, shema, zs_refpm):
    #     self.fenetreMessage(QMessageBox, "info", "before defining the query")
    #     query = """UPDATE temp.cable_al01 cable
    #             SET fb_utile = subquery.cb_fo_util

    #             FROM (SELECT id as cable_id, max(cm_fo_util) as cb_fo_util FROM temp.cable_al01 as cable 
    #             INNER JOIN temp.cheminement_al01 as chem ON ST_length(ST_intersection(cable.geom, chem.geom)) > 0.1
    #             GROUP BY cable_id) AS subquery

    #             WHERE cable.id = subquery.cable_id;"""
    #     self.fenetreMessage(QMessageBox, "info", "The query will be executed")
    #     self.executerRequette(query, False)
    #     self.fenetreMessage(QMessageBox, "info", "The query is executed")


    def calcul_cable_dimensions(self):
        table_name = "cable"
        schema = "temp"
        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()
        self.create_temp_cable_table(schema, table_name, zs_refpm)
        # self.split_cable (schema, table_name, zs_refpm)
        add_columns = "ALTER TABLE temp.cable_" + zs_refpm.split("_")[2] + " ADD COLUMN fb_utile integer; ALTER TABLE temp.cable_" + zs_refpm.split("_")[2] + " ADD COLUMN capacite integer; ALTER TABLE temp.cable_" + zs_refpm.split("_")[2] + " ADD COLUMN Aer_Sou varchar(3);  ALTER TABLE temp.cable_" + zs_refpm.split("_")[2] + " ADD COLUMN ft_bt varchar(3); ALTER TABLE temp.cable_" + zs_refpm.split("_")[2] + " ADD COLUMN type_cable varchar(30); ALTER TABLE temp.cable_" + zs_refpm.split("_")[2] + " ADD COLUMN cb_code integer; "
        self.executerRequette(add_columns, False)
        # self.fenetreMessage(QMessageBox, "info", "After add columns and before calcul_fb_utiles")
        self.calcul_fb_utile_cable(zs_refpm)
        # calculate_distance = """UPDATE temp.cable_al01 cable
        #         SET dist = ST_Length(geom);"""

        # # self.calcul_fb_utiles_cable(shema, zs_refpm)
        # self.fenetreMessage(QMessageBox, "info", "After calcul_fb_utiles")
        # self.executerRequette(calculate_distance, False)
        self.fibre_utile_to_cable_capacity(zs_refpm)
        self.aer_sou(zs_refpm)
        self.ft_bt(zs_refpm)
        self.cable_type(zs_refpm)
        self.update_cb_code(zs_refpm)
        self.add_pg_layer("temp", "cable_" + zs_refpm.split("_")[2].lower())


    def calcul_fb_utile_cable(self, zs_refpm):
        # self.fenetreMessage(QMessageBox, "test", "zs_refpm = ")
        # self.fenetreMessage(QMessageBox, "test", "zs_refpm = " + zs_refpm)
        query = """UPDATE temp.cable_""" + zs_refpm.split("_")[2] + """ cable
                SET fb_utile = subquery.cb_fo_util

                FROM (SELECT id as cable_id, max(cm_fo_util) as cb_fo_util 
                FROM temp.cable_""" + zs_refpm.split("_")[2] + """ as cable 
                INNER JOIN temp.cheminement_""" + zs_refpm.split("_")[2] + """ as chem ON ST_length(ST_intersection(cable.geom, chem.geom)) > 0.1

                GROUP BY cable_id) AS subquery

                WHERE cable.id = subquery.cable_id;"""

        # self.fenetreMessage(QMessageBox, "info", "The query 'calcul_fb_utile_cable will be executed")
        self.executerRequette(query, False)
        self.fenetreMessage(QMessageBox, "info", "The query 'calcul_fb_utile_cable' is executed")


    def aer_sou(self, zs_refpm):
        # self.fenetreMessage(QMessageBox, "info", "aer_sou")
        query = """ UPDATE temp.cable_""" + zs_refpm.split("_")[2] + """ cable
                SET aer_sou = 
                CASE 
                    WHEN 0 = ANY (subquery.cm_code_arr) Then 'A'
                    WHEN 1 = ANY (subquery.cm_code_arr) Then 'A'
                    WHEN 2 = ANY (subquery.cm_code_arr) Then 'A'
                    WHEN 3 = ANY (subquery.cm_code_arr) Then 'A'
                    WHEN 4 = ANY (subquery.cm_code_arr) Then 'A'
                    WHEN 5 = ANY (subquery.cm_code_arr) Then 'A'
                    Else 'S'

                 END

                FROM (SELECT id as cable_id, array_agg(chem.cm_code) as cm_code_arr
                FROM temp.cable_""" + zs_refpm.split("_")[2] + """ as cable 
                INNER JOIN temp.cheminement_""" + zs_refpm.split("_")[2] + """ as chem ON ST_length(ST_intersection(cable.geom, chem.geom)) > 0.1

                GROUP BY cable_id) AS subquery

                WHERE cable.id = subquery.cable_id;"""
        self.executerRequette(query, False)
        # self.fenetreMessage(QMessageBox, "info", "The query is executed")


    def ft_bt(self, zs_refpm):
        query = """UPDATE temp.cable_""" + zs_refpm.split("_")[2] + """ set ft_bt = case
            --WHEN 0 = ANY(subquery.array_pt_code) or 12 = any(subquery.array_pt_code) THEN 'FT'
            WHEN 1 = ANY(subquery.array_pt_code) or 2 = any(subquery.array_pt_code) THEN 'BT'
            ELSE 'FT'
            END    
            FROM (select cable.id, array_agg(ptech.pt_id), array_agg(ptech.pt_code) as array_pt_code
            FROM temp.cable_""" + zs_refpm.split("_")[2] + """ as cable join prod.p_ptech as ptech on ST_DWithin(cable.geom, ptech.geom, 0.0001)
            WHERE ptech.pt_code < 6 or ptech.pt_code in (10, 11, 12)
            GROUP BY cable.id) as subquery

            WHERE temp.cable_""" + zs_refpm.split("_")[2] + """.id = subquery.id; """


        self.executerRequette(query, False)
        # self.fenetreMessage(QMessageBox, "info", "The query of ft_bt is executed")



    def cable_type(self, zs_refpm):
        query = """UPDATE temp.cable_""" + zs_refpm.split("_")[2] + """
                SET type_cable = subquery.case from  (SELECT id, fb_utile, aer_sou, CASE
                    -- WHEN cable.capacite < 432 AND cable.aer_sou = 'S' THEN 'FOS SILEC'
                    -- The new type of cables (TKF)
                    WHEN cable.capacity < 432 AND cable.aer_sou = 'S' THEN 'FO TKF'
                    WHEN cable.capacite = 432 AND cable.aer_sou = 'S' THEN 'FOS ACOME'
                    WHEN cable.capacite >= 432 AND cable.aer_sou = 'S' THEN 'FOS PRYSMIAN'
                    WHEN cable.capacite > 288 AND cable.aer_sou = 'A' THEN 'WARNING!!!'
                    -- WHEN cable.capacite <= 288 AND cable.aer_sou = 'A' AND ft_bt = 'FT' THEN 'FOA SILEC'
                    WHEN cable.capacite <= 288 AND cable.aer_sou = 'A' AND ft_bt = 'FT' THEN 'FO TKF'
                    WHEN cable.capacite <= 288 AND cable.aer_sou = 'A' AND ft_bt = 'BT' THEN 'FOA ACOME'
                END
                FROM temp.cable_""" + zs_refpm.split("_")[2] + """ as cable) subquery
                WHERE temp.cable_""" + zs_refpm.split("_")[2] + """.id = subquery.id;  """
        self.executerRequette(query, False)
        # self.fenetreMessage(QMessageBox, "info", "The query of cable_type is executed")

    def update_cb_code(self, zs_refpm):
        query = """ update temp.cable_""" + zs_refpm.split("_")[2] + """ set cb_code = case
                        WHEN capacite = 12 AND type_cable = 'FOA ACOME' THEN 1
                        WHEN capacite = 24 AND type_cable = 'FOA ACOME' THEN 2
                        WHEN capacite = 48 AND type_cable = 'FOA ACOME' THEN 3
                        WHEN capacite = 72 AND type_cable = 'FOA ACOME' THEN 4
                        WHEN capacite = 96 AND type_cable = 'FOA ACOME' THEN 5
                        WHEN capacite = 144 AND type_cable = 'FOA ACOME' THEN 6
                        WHEN capacite = 288 AND type_cable = 'FOA ACOME' THEN 7
                        WHEN capacite = 432 AND type_cable = 'FOS ACOME' THEN 8
                        WHEN capacite = 576 AND type_cable = 'FOS PRYSMIAN' THEN 9
                        WHEN capacite = 720 AND type_cable = 'FOS PRYSMIAN' THEN 10
                        WHEN capacite = 864 AND type_cable = 'FOS PRYSMIAN' THEN 11
                        -- WHEN capacite = 12 AND type_cable = 'FOA SILEC' THEN 12
                        -- WHEN capacite = 24 AND type_cable = 'FOA SILEC' THEN 13
                        -- WHEN capacite = 48 AND type_cable = 'FOA SILEC' THEN 14
                        -- WHEN capacite = 72 AND type_cable = 'FOA SILEC' THEN 15
                        -- WHEN capacite = 96 AND type_cable = 'FOA SILEC' THEN 16
                        -- WHEN capacite = 144 AND type_cable = 'FOA SILEC' THEN 17
                        -- WHEN capacite = 288 AND type_cable = 'FOA SILEC' THEN 18
                        -- WHEN capacite = 12 AND type_cable = 'FOS SILEC' THEN 19
                        -- WHEN capacite = 24 AND type_cable = 'FOS SILEC' THEN 20
                        -- WHEN capacite = 48 AND type_cable = 'FOS SILEC' THEN 21
                        -- WHEN capacite = 72 AND type_cable = 'FOS SILEC' THEN 22
                        -- WHEN capacite = 96 AND type_cable = 'FOS SILEC' THEN 23
                        -- WHEN capacite = 144 AND type_cable = 'FOS SILEC' THEN 24
                        -- WHEN capacite = 288 AND type_cable = 'FOS SILEC' THEN 25
                        WHEN capacite = 12 AND type_cable = 'FO TKF' THEN 27
                        WHEN capacite = 24 AND type_cable = 'FO TKF' THEN 28
                        WHEN capacite = 36 AND type_cable = 'FO TKF' THEN 29
                        WHEN capacite = 48 AND type_cable = 'FO TKF' THEN 30
                        WHEN capacite = 72 AND type_cable = 'FO TKF' THEN 31
                        WHEN capacite = 96 AND type_cable = 'FO TKF' THEN 32
                        WHEN capacite = 144 AND type_cable = 'FO TKF' THEN 33
                        WHEN capacite = 288 AND type_cable = 'FO TKF' THEN 34
                    END"""

        self.executerRequette(query, False)
        # self.fenetreMessage(QMessageBox, "info", "The query of update_cb_code is executed")


    def update_p_cheminement(self):
        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()
        query_update_chem = """
        -- mettre a jour la geometrie
        UPDATE prod.p_cheminement SET geom = tempo.geom, cm_fo_util = tempo.cm_fo_util
        FROM temp.cheminement_""" + zs_refpm.split("_")[2] + """ as tempo
        WHERE prod.p_cheminement.cm_id = tempo.cm_id;

        -- mettre a jour fibre util sauf pour les cheminements commun entre plus qu'un SRO
        /*UPDATE prod.p_cheminement SET cm_fo_util = tempo2.cm_fo_util
        FROM temp.cheminement_""" + zs_refpm.split("_")[2] + """ as tempo2
        WHERE prod.p_cheminement.cm_id = tempo2.cm_id AND prod.p_cheminement.cm_zs_code NOT LIKE '%,%';*/

        UPDATE prod.p_cheminement SET cm_fo_util = tempo2.cm_fo_util
        FROM temp.cheminement_""" + zs_refpm.split("_")[2] + """ as tempo2
        WHERE prod.p_cheminement.cm_id = tempo2.cm_id



        -- mettre a jour fibre util dans les cheminements commun entre plus qu'un SRO
        /*UPDATE prod.p_cheminement SET cm_fo_util = tempo3.the_sum
        FROM (select c2.cm_id, count(*), sum(c1.cm_fo_util) as the_sum from prod.p_cheminement as c1,
            (select * from prod.p_cheminement where cm_zs_code like '%,%' and cm_zs_code like '%""" + zs_refpm.split("_")[2]  + """%') c2
            where ST_DWithin(ST_EndPoint(c2.geom), ST_StartPoint(c1.geom), 0.0001)
            group by c2.cm_id) AS tempo3
        WHERE prod.p_cheminement.cm_id = tempo3.cm_id;*/



        """

        query_update_chem_commun = """
            Do
            $$
            DECLARE
            quad varchar;
            the_array varchar[];
            id integer;
            zs_code varchar;
            fo_util integer;


            BEGIN

            UPDATE prod.p_cheminement SET cm_fo_util = 0  WHERE cm_zs_code LIKE '%,%' AND cm_typelog IN ('RA','DI','TD');

            FOR id, zs_code, the_array, fo_util IN SELECT c.cm_id, c.cm_zs_code, string_to_array(c.cm_zs_code, ', ') as the_array, c.cm_fo_util FROM prod.p_cheminement as c WHERE c.cm_zs_code LIKE '%,%' AND c.cm_typelog IN ('RA','DI','TD')
            LOOP 

                FOREACH quad in array the_array
                LOOP
                    RAISE NOTICE 'the array : %, quad : %', the_array, quad;

                    IF (SELECT EXISTS (
                       SELECT *
                       FROM   information_schema.tables 
                       WHERE  table_schema = 'temp'
                       AND    table_name LIKE 'cheminement_' || lower(quad)
                       )) THEN RAISE NOTICE 'table cheminement_% exists', lower(quad);
                       EXECUTE 'UPDATE prod.p_cheminement set cm_fo_util = cm_fo_util + (SELECT cm_fo_util from temp.cheminement_' || lower(quad) || ' WHERE cm_id = ' || id || ' ) where cm_id = ' || id;         
                    END IF;
                END LOOP;
                
            END LOOP;
                
            END;
            $$
            language plpgsql;"""


        self.executerRequette(query_update_chem, False)
        self.executerRequette(query_update_chem_commun, False)
        self.fenetreMessage(QMessageBox, "info", "The table p_cheminement is updated")


    def update_p_cable(self):
        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()
        query_update_cable = """INSERT INTO prod.p_cable(cb_code, geom, cb_comment)
                                 SELECT cb_code, ST_LineMerge(geom), '""" + zs_refpm.split("_")[2] + """' from temp.cable_""" + zs_refpm.split("_")[2] + """  
                                 WHERE id not in (SELECT cable.id FROM temp.cable_""" + zs_refpm.split("_")[2] + """ as cable 
                                 JOIN prod.p_sitetech as stech ON ST_Dwithin(cable.geom, stech.geom, 0.0001))"""
        try:
            # self.fenetreMessage(QMessageBox, "info", "The query will be executed")
            self.executerRequette(query_update_cable, False)
            if not self.isMultistring:
                self.fenetreMessage(QMessageBox, "info", "The table p_cable is updated ")
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage", str(e))


    def copy_style(self, source, dest):
        try:
            source_layer = QgsMapLayerRegistry.instance().mapLayersByName(source)[0]
            self.iface.setActiveLayer(source_layer)
            self.iface.actionCopyLayerStyle().trigger()
            dest_layer = QgsMapLayerRegistry.instance().mapLayersByName(dest)[0]
            self.iface.setActiveLayer(dest_layer)
            self.iface.actionPasteLayerStyle().trigger()
        except Exception as e:
            # self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage",str(e))
            return





