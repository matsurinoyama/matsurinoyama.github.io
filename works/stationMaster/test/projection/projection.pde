PImage img;
int cols = 7;
int rows = 7;

PVector[][] points;
int draggedI = -1, draggedJ = -1;
float dragThreshold = 10;
boolean editMode = true;
boolean dragAllMode = false;
PVector dragAllOffset = new PVector(0, 0);

ArrayList<String> imageFiles;
int currentImageIndex = 0;
int lastImageChange = 0;
int imageChangeInterval = 5000; // 5 seconds

void setup() {
  fullScreen(P3D);
  
  // Load all aligned images
  loadImageFiles();
  
  if (imageFiles.size() > 0) {
    img = loadImage(imageFiles.get(0));
  } else {
    println("No images found with prefix 'aligned_' in faces folder");
    exit();
  }
  
  resetPoints();
  
  // Automatically load saved coordinates if available
  loadCoordinates();
  
  lastImageChange = millis();
}

void loadImageFiles() {
  imageFiles = new ArrayList<String>();
  File dir = new File(sketchPath("../../faces"));
  
  if (dir.exists() && dir.isDirectory()) {
    File[] files = dir.listFiles();
    for (File file : files) {
      String name = file.getName();
      if (name.startsWith("aligned_") && (name.endsWith(".jpg") || name.endsWith(".png") || name.endsWith(".jpeg"))) {
        imageFiles.add("../../faces/" + name);
      }
    }
  }
  
  if (imageFiles.size() > 0) {
    println("Found " + imageFiles.size() + " images");
  }
}

void resetPoints() {
  points = new PVector[rows][cols];
  float w = width * 0.4;
  float h = height * 0.6;
  float startX = (width - w) / 2;
  float startY = (height - h) / 2;

  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      float x = map(i, 0, cols-1, startX, startX + w);
      float y = map(j, 0, rows-1, startY, startY + h);
      points[j][i] = new PVector(x, y, 0);
    }
  }
}

void draw() {
  // Change image every 5 seconds
  if (millis() - lastImageChange > imageChangeInterval && imageFiles.size() > 1) {
    currentImageIndex = (currentImageIndex + 1) % imageFiles.size();
    img = loadImage(imageFiles.get(currentImageIndex));
    lastImageChange = millis();
    println("Switched to image: " + imageFiles.get(currentImageIndex));
  }
  
  background(0);
  noStroke();
  noFill();
  textureMode(IMAGE);
  beginShape(QUADS);
  texture(img);

  // Draw the mesh (texture mapped)
  for (int j = 0; j < rows - 1; j++) {
    for (int i = 0; i < cols - 1; i++) {
      float u1 = i / float(cols - 1);
      float v1 = j / float(rows - 1);
      float u2 = (i + 1) / float(cols - 1);
      float v2 = (j + 1) / float(rows - 1);

      PVector p1 = points[j][i];
      PVector p2 = points[j][i + 1];
      PVector p3 = points[j + 1][i + 1];
      PVector p4 = points[j + 1][i];

      vertex(p1.x, p1.y, p1.z, u1 * img.width, v1 * img.height);
      vertex(p2.x, p2.y, p2.z, u2 * img.width, v1 * img.height);
      vertex(p3.x, p3.y, p3.z, u2 * img.width, v2 * img.height);
      vertex(p4.x, p4.y, p4.z, u1 * img.width, v2 * img.height);
    }
  }
  endShape();

  // Draw editable points
  if (editMode) {
    stroke(255, 50);
    for (int j = 0; j < rows; j++) {
      for (int i = 0; i < cols; i++) {
        if (i < cols - 1) line(points[j][i].x, points[j][i].y, points[j][i + 1].x, points[j][i + 1].y);
        if (j < rows - 1) line(points[j][i].x, points[j][i].y, points[j + 1][i].x, points[j + 1][i].y);
      }
    }
    noStroke();
    fill(255, 0, 0);
    for (int j = 0; j < rows; j++) {
      for (int i = 0; i < cols; i++) {
        ellipse(points[j][i].x, points[j][i].y, 10, 10);
      }
    }
  }
}

void mousePressed() {
  if (!editMode) return;
  
  if (dragAllMode) {
    dragAllOffset.x = mouseX;
    dragAllOffset.y = mouseY;
    return;
  }
  
  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      if (dist(mouseX, mouseY, points[j][i].x, points[j][i].y) < dragThreshold) {
        draggedI = i;
        draggedJ = j;
        return;
      }
    }
  }
}

void mouseDragged() {
  if (dragAllMode) {
    float dx = mouseX - dragAllOffset.x;
    float dy = mouseY - dragAllOffset.y;
    
    for (int j = 0; j < rows; j++) {
      for (int i = 0; i < cols; i++) {
        points[j][i].x += dx;
        points[j][i].y += dy;
      }
    }
    
    dragAllOffset.x = mouseX;
    dragAllOffset.y = mouseY;
  } else if (draggedI != -1 && draggedJ != -1) {
    points[draggedJ][draggedI].x = mouseX;
    points[draggedJ][draggedI].y = mouseY;
  }
}

void mouseReleased() {
  draggedI = -1;
  draggedJ = -1;
}

void keyPressed() {
  if (key == 'r') resetPoints();
  if (key == 'e') editMode = !editMode;
  if (key == 'a') dragAllMode = !dragAllMode;

  // Save coordinates with Shift+S
  if (key == 'S') {
    saveCoordinates();
  }

  // Load coordinates with Shift+R
  if (key == 'R') {
    loadCoordinates();
  }

  // Scale mesh vertices around centroid
  if (key == '+') {
    scaleMesh(1.05); // scale up 5%
  }
  if (key == '-') {
    scaleMesh(0.95); // scale down 5%
  }
}

void saveCoordinates() {
  PrintWriter output = createWriter("mesh_coordinates.txt");
  output.println(rows + "," + cols);
  
  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      output.println(points[j][i].x + "," + points[j][i].y + "," + points[j][i].z);
    }
  }
  
  output.flush();
  output.close();
  println("Coordinates saved to mesh_coordinates.txt");
}

void loadCoordinates() {
  File f = new File(dataPath("mesh_coordinates.txt"));
  if (!f.exists()) {
    f = new File(sketchPath("mesh_coordinates.txt"));
  }
  
  if (!f.exists()) {
    println("No saved coordinates found");
    return;
  }
  
  String[] lines = loadStrings("mesh_coordinates.txt");
  if (lines.length < 1) {
    println("Invalid coordinate file");
    return;
  }
  
  String[] dimensions = split(lines[0], ',');
  int savedRows = int(dimensions[0]);
  int savedCols = int(dimensions[1]);
  
  if (savedRows != rows || savedCols != cols) {
    println("Warning: Saved dimensions don't match current mesh");
    return;
  }
  
  int lineIndex = 1;
  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      if (lineIndex < lines.length) {
        String[] coords = split(lines[lineIndex], ',');
        points[j][i].x = float(coords[0]);
        points[j][i].y = float(coords[1]);
        points[j][i].z = float(coords[2]);
        lineIndex++;
      }
    }
  }
  
  println("Coordinates loaded from mesh_coordinates.txt");
}

void scaleMesh(float factor) {
  // Compute centroid of all points
  float cx = 0, cy = 0, cz = 0;
  int count = rows * cols;
  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      cx += points[j][i].x;
      cy += points[j][i].y;
      cz += points[j][i].z;
    }
  }
  cx /= count;
  cy /= count;
  cz /= count;

  // Scale each point around centroid
  for (int j = 0; j < rows; j++) {
    for (int i = 0; i < cols; i++) {
      PVector p = points[j][i];
      p.x = cx + (p.x - cx) * factor;
      p.y = cy + (p.y - cy) * factor;
      p.z = cz + (p.z - cz) * factor;
    }
  }
}
