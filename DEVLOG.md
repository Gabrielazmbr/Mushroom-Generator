## Stage #1.0

I organized the project structure and created the initial files. Started by developing my mushroom class and two functions for stem and cap generation.

I had to look for ways to create the basic geometry. A curve for the stem, and a half a sphere for the cap. I researched Hermit curves and found that they are a type of cubic Hermite spline, which can be used to create smooth curves with control points. I actually found some Houdini examples in Professor Jiang Chang learning materials.
- https://brightspace.bournemouth.ac.uk/d2l/le/lessons/579329/topics/2326571

I decided to give it a go to create the curve I needed for my stem. I also did some research on numpy's documentation on linspace and other useful functions to create and compute the points for the curve, such as np.array and np.outer
- https://numpy.org/devdocs/reference/generated/numpy.linspace.html

For the half sphere I found some examples and tutorials on how to use numpy to create them. I used the np.linspace to compute initial angles and np.outer to arrange the x,y,z coordinates of the half sphere.Then I used flatten to collect the coordinates in a single array.

Lastly, I used pyVista to temporaly visualize the geometry I was creating.

Next steps:
- Generate a mesh based on the coordinates of the stem and cap.
- Explore CGALS - 3D Mesh Generation for realistic mesh generation -> https://doc.cgal.org/latest/Mesh_3/index.html#Chapter_3D_Mesh_Generation
- Simulate growth of the mushroom.
- Explore variations with noise and different geometry.



## Stage #1.1

Here is an example diagram of what I think classes and structure should look like in the future.

```text
                                     +-----------------------------+
                                     |        mushroomgen/         |
                                     +-----------------------------+
                                                    |
                                                    v
+------------------+       +------------------+          +------------------+        +------------------+
|      core/       |       |   generators/    |          |   variations/    |        |     render/      |
+------------------+       +------------------+          +------------------+        +------------------+
          |                          |                            |                            |
          v                          v                            v                            v
+--------------------+  +-------------------------+   +--------------------------+   +--------------------------+
| Species Class      |  | L-System Class          |   | Noise Variations Class   |   | OpenGL anim Class        |
| Variation Class    |  | Curves Class            |   | Color Variations Class   |   | Materials Class          |
| Mesh Build Class   |  | Physics Class           |   | Scale Variations Class   |   | Camera Class             |
| Terrain Class      |  | Geometry Class          |   | Terrain Variations Class |   | Render / Light Class     |
+--------------------+  +-------------------------+   +--------------------------+   +--------------------------+

```
**Module Overview:**
- Core/ : Here is where I control mushrooms parameters (linked to species), build geometry, mesh and make terrain for mushrooms. A variation class could be helpful to centralice and control variations I need.
- Generators/ : This will help create the geometry of mushrooms
- Variations/ : This will help modify existing mushrooms
- Render/ : Using OpenGL to visualize, add materials, lighting and render


**Updates:**
- Species Class
  - I did a first version of the species class. Created FLY_AGARIC for testing purposes. For now I have some stem and cap attributes plus some resolution defaults.
- Curves Class
  - I made a curves class, with the purpose of creating different types of curves for different purposes. There could be different styles for stems and caps. Although I am not sure if mixing curves for different geometry is scalable, it could be a good idea to have a separate class for each type of geometry.
- Geometry generator
  - My geometry generator stays the same. Hermite curves have worked for what I need for now. I attempted to create the cap using curves, so I might not use half a sphere for the base.
- Build Class
  - Created a build class that uses curves to place geometry. For the stem I researched Parallel transport and Frenet–Serret formulas, that basically make a tube based on rings along the curve points that then are connected by triangle faces.
-- https://en.wikipedia.org/wiki/Frenet%E2%80%93Serret_formulas
-- https://en.wikipedia.org/wiki/Parallel_transport?utm_source=chatgpt.com
-- https://www.youtube.com/watch?v=40r56pX4mqA&t=207s
I still think there might be a simpler way to achieve this, but I'm not sure what it is yet.

**Research & References**
- I found some more Houdini tutorials on Mushrooms. I liked this one because it avoids complex geometry and still gets nice results. It is also very detailed but quite long.
-- https://www.patreon.com/posts/mushroom-part-i-86741805?collection=244963

- I was thinking about using CGAL for gills, as they are quite complex geometry and found pygalmesh
-- https://pypi.org/project/pygalmesh/?utm_source=chatgpt.com
It might be a good fit — it exposes CGAL’s meshing features through a Python frontend.



## Stage #2.0

**Updates:**
- Build Class Changes
  - I did a second version of the build class, separating geometry generation from mesh generation. I think it is more clear now, as I can spot easier if I have a problem with geometries or meshes.
  - I did a first attempt of gills, trying to keep it simple, but it does not look good. I also think topology wise, is not the best approach. I will try to make them with l-systems.
  - I made a function to stack everything together. It works, although I need to do some research on how to properly translate, rotate, and scale meshes in world axis. For now I just moved the cap and gills points at the beginning of buildCap to match the endpoints of the stem. That messed up the noise I had in my meshes, so I have to find a better solution. 
- NoiseFields
  - I found a noise library that can help me implement perlin noise and simplex noise into the meshes. I created a class that acts as a wrapper of it.
- Updated toml
  - Updated my toml file, as I was missing -> "pyvista>=0.46.4"
- Small updates in my tests
 - I modified my tests according to the modifications I did in my Build class.
 - Some tests are currently failing because of how I made the translation of the Cap. 

**Research & References**
- Noise Library: https://pypi.org/project/noise/
- Simplex noise and perlin noise: https://www.researchgate.net/publication/216813608_Simplex_noise_demystified // https://www.youtube.com/watch?v=DxUY42r_6Cg 
- More on mushroom gills : https://www.sidefx.com/tutorials/houdini-algorithmic-live-mushroom-gills/ 

Next steps:
- OpenGL implementation, as I already have a mushroom mesh to test. 
- Improve Gills method and add more details to the Mushroom.
- Fix my noiseFields / world/local axis implementation. 
- Writing additional tests



## Stage #2.1

**Updates:**
- I started implementing OpenGL. I followed the example seen in class and created a MainWindow class inside my render folder, along with some initial shaders.
- I had to convert my meshes into uint32/float32 as they were int64/float64 originally. I also computed the normals for each mesh.
- I created an (N,6) array to store vertex positions and normals and tried to center and scale my mushroom to be seen correctly (It needs tunning.)
- Created a VAO and used the simple shaders seen in class to display the mesh. I am missing a basic lighting / better shaders system to get the shape and detail of the visual appearance of the mesh.
- I fixed the translation of the Cap and Gills points to match the endpoints of the Stem in the buildMushroom method (not before) and avoided those weird artifacts generated because of bad axis implementation.



## Stage #3.0
**Updates:**
- Build Class Changes
  - I made improvements to my gills mesh. This time I went with a different approach based on a small research on lamellate morphology. I discarted l-systems and prefered to go for unbranched gills that climbed from the outer to the center of the cap. After having the initial curves, a plane is extruded by calculating a second curve beneath the original. Then thickness is added and vertices and faces are assembled in a similar process to the cap and the stem. 
  - I changed my stem look and approach to it. As catmull-rom splines give me a better flexibility to add some more detail. This time I tried to develop a more accurate shape that included a suggested stem ring and a more realistic base.
  - I fixed the normals for the stem and gills meshes.
- Curves Class Changes
  - I made a new curve to be able to draw the stem. For future variations I will be adding more types of curves to shape different variations of stems and caps. 
- OpenGl Main Window Changes
  - I improved considerably my coordinate systems and centered my model view to my camera view and projection. That also helped fixing my face culling issue.
  - Added a temporal diffuse shader from ncca.ngl to improve the lighting and shading of the mushroom. 
  - Added more keypress events and mouse controls based on several PyNglDemos examples.  
  
**Research & References**
- Coordinate Systems in OpenGL
  - http
- Coordinate Systems in OpenGL
  - https://learnopengl.com/Getting-started/Coordinate-Systems
  - https://learnopengl.com/code_viewer_gh.php?code=src/1.getting_started/6.3.coordinate_systems_multiple/coordinate_systems_multiple.cpp
  - https://github.com/NCCA/PyNGLDemos
- Face Culling in OpenGL
  - https://wikis.khronos.org/opengl/Face_Culling 
  - https://learnopengl.com/Advanced-OpenGL/Face-culling
- Gills and Stem research
  - Full mushrooms out of a line: https://inria.hal.science/inria-00355626v1/document 
  - Lamellate Morphology: https://pmc.ncbi.nlm.nih.gov/articles/PMC2891949/
  - Houdini procedural gills: https://www.youtube.com/watch?v=FNC1uLJGjag&t=447s 

**Next steps:**
- Implementing more complex Shaders in OpenGL.
- Enhance and fix some issues with my Noise fields. 
- Start implementing variations of the mushroom. 
- Add final details, like scales or spores.
- Update and add tests.



## Stage #3.1
**Updates:**
- Build Class Changes
  - I added Scales to the mushroom by scattering Sphere like meshes into the outer cap mesh. I also added properties like the streng of the noise in the shapes, the scale and the amount. 
  - I implemented a function to export my mushroom as an OBJ file. This functionality allows to be able to open my mushroom inside houdini or maya. A QT button is present in the interface to activate the function. 
  - Updated my buildMushroomMesh function to add scales and refine the stitiching to export a proper mesh to opengl. 
  - Debug and small improvements to my gills and cap. As there was a mismatch between the innercap inside the BuildCapMesh function and the inner_cap calculated in the BuildGills function. 
- Curves Class Changes
  - I added new variations for the Stem and the Cap. These variations will be picked by the user in the interface. Updated my generator function accordingly. 
- OpenGL Class Changes
  - Started implementing QT interface and added some basic parameters (updatable) to the inerface. 
  - I added PBR frgament / vertex shading. These allowed to properly view the mushroom with colors and refinement for each part.  Added 3 light sources to the scene. 
  - Added a rebuilt function for thr mushroom to be properly updated each time the user makes a change in the interface. 
  - Updated PaintGL and my VAO accordingly. 
- Tests
  - Updated and added new tests for new functions in build class, curves class and geometry class. 

  

**Next steps:**
- Refine and add missing parameters to the QT interface.
- Update Species class
- Add missing references and update Readme. 
- Improving shaders and fix normals issues.



## Stage #3.2
**Updates:**
- Updated the QT interface to include all the parameters to generate a  mushroom and refine it.
- Updated README.md to include overview of the project and references.
- Organiced species class.

**Next steps:**
- Adding more mushroom species.
