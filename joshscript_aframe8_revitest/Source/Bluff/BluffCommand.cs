using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Web.Script.Serialization;
using Autodesk.Revit.UI;
using Autodesk.Revit.DB;
using Autodesk.Revit.Attributes;

namespace Bluff
{
    [Transaction(TransactionMode.Manual)]
    public class BluffCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            Document doc = commandData.Application.ActiveUIDocument.Document;
            
            // Create debug log file
            string logPath = Path.Combine(Path.GetTempPath(), "Bluff_Addin_Debug.txt");
            var logWriter = new StreamWriter(logPath, false);
            logWriter.WriteLine($"Bluff Add-in v1.5 Debug Log - {DateTime.Now}");
            logWriter.WriteLine(new string('=', 50));
            logWriter.WriteLine("USING LATEST JSON DATA WITH TRANSFORMED COORDINATES");
            logWriter.WriteLine("Source: cone_data.json (351 positions)");
            logWriter.WriteLine("Heights: From PTS data with Z-axis scaling (3.28084)");
            logWriter.WriteLine(new string('=', 50));
            
            // Plugin loaded successfully - no popup needed
            
            try
            {
                // Read cone data from JSON file
                var coneData = ReadConeData();
                if (coneData == null || coneData.Cones == null || coneData.Cones.Count == 0)
                {
                    message = "Bluff Add-in v1.3: No cone data found or failed to read cone_data-3.json";
                    return Result.Failed;
                }
                
                using (Transaction trans = new Transaction(doc, "Place Sphere Markers from Cone Data"))
                {
                    trans.Start();
                    
                    // 1. Find the family symbol (sphere family)
                    FamilySymbol familySymbol = FindSphereFamily(doc);
                    if (familySymbol == null)
                    {
                        message = "Bluff Add-in v1.3: No family symbols found in project. Please load any family (e.g., ASB_Anno_ClashMark3D.rfa) into the project.";
                        return Result.Failed;
                    }
                    
                    // 2. Activate the family symbol
                    if (!familySymbol.IsActive)
                    {
                        familySymbol.Activate();
                        doc.Regenerate();
                    }
                    
                    // 3. Get the first level for proper placement
                    Level firstLevel = new FilteredElementCollector(doc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .OrderBy(l => l.Elevation)
                        .FirstOrDefault();
                    
                    if (firstLevel != null)
                    {
                        logWriter.WriteLine($"Using level: {firstLevel.Name} (Elevation: {firstLevel.Elevation:F2} ft)");
                    }
                    
                    // 4. Calculate Z-coordinate transformation based on actual data
                    var zValues = coneData.Cones
                        .Where(c => c.dxf_position != null)
                        .Select(c => c.dxf_position.z)
                        .ToList();
                    
                    double minZ = zValues.Min();
                    double maxZ = zValues.Max();
                    double zRange = maxZ - minZ;
                    
                    logWriter.WriteLine($"Z-coordinate analysis: min={minZ:F2}m, max={maxZ:F2}m, range={zRange:F2}m");
                    logWriter.WriteLine($"NOTE: These are ORIENTED heights from gravity-corrected COLMAP data");
                    
                    // Z values are already correctly oriented from COLMAP reconstruction
                    // No offset needed - use Z values directly
                    double zOffset = 0.0; // No offset - Z values are already correct
                    logWriter.WriteLine($"Using Z values directly (no offset needed)");
                    logWriter.WriteLine($"Z range: {minZ:F2}m to {maxZ:F2}m");
                    
                    // 5. Place instances at coordinates
                    int placedCount = 0;
                    logWriter.WriteLine($"Placing {coneData.Cones.Count} sphere instances...");
                    logWriter.WriteLine("\nSample coordinate transformations (showing range):");
                    logWriter.WriteLine("Format: DXF(m) → Revit(feet) | Final XYZ");
                    
                    // Calculate sample indices to show range (first, 25%, 50%, 75%, last)
                    int totalCones = coneData.Cones.Count;
                    int[] sampleIndices = { 0, totalCones / 4, totalCones / 2, (3 * totalCones) / 4, totalCones - 1 };
                    int sampleCount = 0;
                    int currentIndex = 0;
                    
                    foreach (var cone in coneData.Cones)
                    {
                        if (cone.dxf_position != null)
                        {
                            // Convert DXF coordinates (meters) to Revit XYZ (feet)
                            // Apply 180-degree rotation around origin: (x,y) -> (-x,-y)
                            double xFeet = -cone.dxf_position.x * 3.28084;
                            double yFeet = -cone.dxf_position.y * 3.28084;
                            // Apply calculated Z offset to bring points to appropriate level
                            double zFeet = (firstLevel != null ? firstLevel.Elevation : 0) + 
                                          (cone.dxf_position.z + zOffset) * 3.28084;
                            
                            XYZ point = new XYZ(xFeet, yFeet, zFeet);
                            
                            // Log sample coordinate transformations for range
                            if (sampleIndices.Contains(currentIndex))
                            {
                                string position = sampleCount == 0 ? "First" : 
                                               sampleCount == 1 ? "25%" : 
                                               sampleCount == 2 ? "50%" : 
                                               sampleCount == 3 ? "75%" : "Last";
                                logWriter.WriteLine($"  {position} (#{currentIndex + 1}): DXF({cone.dxf_position.x:F2}, {cone.dxf_position.y:F2}, {cone.dxf_position.z:F2}) → " +
                                    $"Revit({xFeet:F2}, {yFeet:F2}, {zFeet:F2}) | Final XYZ({point.X:F2}, {point.Y:F2}, {point.Z:F2})");
                                sampleCount++;
                            }
                            
                            // Create family instance with level
                            FamilyInstance instance = doc.Create.NewFamilyInstance(
                                point, familySymbol, firstLevel, null, 0);
                            
                            if (instance != null)
                                placedCount++;
                        }
                        currentIndex++;
                    }
                    
                    logWriter.WriteLine($"Successfully placed {placedCount} instances");
                    
                    trans.Commit();
                    
                    // Close log file and show debug popup
                    logWriter.WriteLine($"\nLog completed at {DateTime.Now}");
                    logWriter.Close();
                    
                    // Show debug log in notepad
                    System.Diagnostics.Process.Start("notepad.exe", logPath);
                    
                    return Result.Succeeded;
                }
            }
            catch (Exception ex)
            {
                logWriter.WriteLine($"\nERROR: {ex.Message}");
                logWriter.WriteLine($"Stack trace: {ex.StackTrace}");
                logWriter.Close();
                
                // Show debug log in notepad for errors too
                System.Diagnostics.Process.Start("notepad.exe", logPath);
                message = $"Bluff Add-in v1.3 Error: {ex.Message}";
                return Result.Failed;
            }
        }
        
        private FamilySymbol FindSphereFamily(Document doc)
        {
            // Find sphere family - simplified
            var familySymbols = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>();
            
            // Look for common sphere family names
            string[] sphereNames = { "ASB_Anno_ClashMark3D", "Sphere", "Ball", "Marker", "Point" };
            
            foreach (string name in sphereNames)
            {
                var symbol = familySymbols.FirstOrDefault(fs => 
                    fs.FamilyName.ToLower().Contains(name.ToLower()) || 
                    fs.Name.ToLower().Contains(name.ToLower()));
                if (symbol != null)
                    return symbol;
            }
            
            // Return first available family if no sphere found
            return familySymbols.FirstOrDefault();
        }
        
        private ConeData ReadConeData()
        {
            try
            {
                // Hardcoded full path to the JSON file
                string jsonPath = @"C:\Users\JoshuaLumley\Dropbox\0000 Github Repos\asBuilt_DataColmap\paul\joshscript_aframe8_revitest\cone_data.json";
                
                if (!File.Exists(jsonPath))
                {
                    System.Diagnostics.Debug.WriteLine($"JSON file not found at: {jsonPath}");
                    return null;
                }
                
                string jsonContent = File.ReadAllText(jsonPath);
                var serializer = new JavaScriptSerializer();
                return serializer.Deserialize<ConeData>(jsonContent);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error reading cone data: {ex.Message}");
                return null;
            }
        }
    }
    
    // Data classes for JSON deserialization
    public class ConeData
    {
        public ExportInfo ExportInfo { get; set; }
        public List<Cone> Cones { get; set; }
    }
    
    public class ExportInfo
    {
        public string Timestamp { get; set; }
        public int TotalCones { get; set; }
        public string SourceGeojson { get; set; }
        public double BasePointNorthing { get; set; }
        public double BasePointEasting { get; set; }
        public double BasePointElevation { get; set; }
        public double BasePointAngleToTrueNorth { get; set; }
    }
    
    public class Cone
    {
        public int cone_id { get; set; }
        public DxfPosition dxf_position { get; set; }
        public Direction direction { get; set; }
        public int camera_index { get; set; }
        public int frame_number { get; set; }
        public string image_path { get; set; }
        public object metadata { get; set; }
    }
    
    public class DxfPosition
    {
        public double x { get; set; }
        public double y { get; set; }
        public double z { get; set; }
    }
    
    public class Direction
    {
        public Forward up { get; set; }
        public Forward forward { get; set; }
    }
    
    public class Forward
    {
        public double x { get; set; }
        public double y { get; set; }
        public double z { get; set; }
    }
}
