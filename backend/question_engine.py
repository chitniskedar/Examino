"""
question_engine.py — Generate structured questions from text.
Pre-loaded question banks for all 8 PESU 1st-year subjects:
  Chemistry, EEE, EPD, EVS, MES, Physics, Python, Statics
"""

import random
import uuid
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
#  PRE-LOADED SUBJECT QUESTION BANKS
# ═══════════════════════════════════════════════════════════════════════════════

SUBJECT_BANKS: dict[str, list[dict]] = {

    # ── CHEMISTRY ─────────────────────────────────────────────────────────────
    "Chemistry": [
        # Unit 1 – Electrochemistry & Corrosion
        {"type":"mcq","q":"Which of the following is the correct expression for the Nernst equation?","opts":["E = E° - (RT/nF)lnQ","E = E° + (RT/nF)lnQ","E = E° × (RT/nF)lnQ","E = E° / (RT/nF)lnQ"],"a":"E = E° - (RT/nF)lnQ","topic":"Electrochemistry","unit":"Unit-1","diff":"medium"},
        {"type":"tf","q":"The standard hydrogen electrode (SHE) has a reduction potential of 0 V by convention.","a":"True","topic":"Electrochemistry","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"Which type of corrosion involves two dissimilar metals in electrical contact in an electrolyte?","opts":["Uniform corrosion","Galvanic corrosion","Pitting corrosion","Crevice corrosion"],"a":"Galvanic corrosion","topic":"Corrosion","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"In a galvanic cell, oxidation occurs at the cathode.","a":"False","topic":"Electrochemistry","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"The unit of specific conductance (conductivity) is:","opts":["Ω·m","S·m⁻¹","S·m","Ω⁻¹"],"a":"S·m⁻¹","topic":"Electrochemistry","unit":"Unit-1","diff":"medium"},
        {"type":"mcq","q":"Sacrificial anode method of corrosion prevention uses which metal?","opts":["Copper","Gold","Zinc","Platinum"],"a":"Zinc","topic":"Corrosion","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"Molar conductance increases with dilution for strong electrolytes.","a":"True","topic":"Electrochemistry","unit":"Unit-1","diff":"medium"},
        {"type":"mcq","q":"EMF of a cell depends on:","opts":["Temperature only","Concentration only","Both temperature and concentration","Neither"],"a":"Both temperature and concentration","topic":"Electrochemistry","unit":"Unit-1","diff":"medium"},
        # Unit 2 – Spectroscopic & Analytical Techniques
        {"type":"mcq","q":"In UV-Vis spectroscopy, which transition is responsible for absorption in organic compounds?","opts":["σ→σ*","n→σ*","π→π*","All of the above"],"a":"All of the above","topic":"Spectroscopy","unit":"Unit-2","diff":"hard"},
        {"type":"tf","q":"Beer-Lambert law states that absorbance is inversely proportional to concentration.","a":"False","topic":"Spectroscopy","unit":"Unit-2","diff":"easy"},
        {"type":"mcq","q":"Which spectroscopic technique is used to determine the structure of organic compounds based on nuclear spin?","opts":["UV-Vis","IR","NMR","Mass Spectrometry"],"a":"NMR","topic":"Spectroscopy","unit":"Unit-2","diff":"easy"},
        {"type":"mcq","q":"The fingerprint region in IR spectroscopy lies in the range:","opts":["4000–2500 cm⁻¹","2500–2000 cm⁻¹","2000–1500 cm⁻¹","1500–600 cm⁻¹"],"a":"1500–600 cm⁻¹","topic":"Spectroscopy","unit":"Unit-2","diff":"hard"},
        # Unit 3 – Polymers
        {"type":"mcq","q":"Which of the following is an example of an addition polymer?","opts":["Nylon-6,6","Bakelite","Polyethylene","Dacron"],"a":"Polyethylene","topic":"Polymers","unit":"Unit-3","diff":"easy"},
        {"type":"tf","q":"Vulcanisation of rubber involves cross-linking rubber chains with sulphur.","a":"True","topic":"Polymers","unit":"Unit-3","diff":"easy"},
        {"type":"mcq","q":"The degree of polymerisation is defined as:","opts":["Molecular weight / monomer weight","Number of repeat units in a polymer chain","Number of monomers available","Cross-link density"],"a":"Number of repeat units in a polymer chain","topic":"Polymers","unit":"Unit-3","diff":"medium"},
        {"type":"mcq","q":"Which polymer is used in bulletproof vests?","opts":["PVC","Kevlar","Nylon-6","Teflon"],"a":"Kevlar","topic":"Polymers","unit":"Unit-3","diff":"medium"},
        # Unit 4 – Water Treatment
        {"type":"mcq","q":"Temporary hardness of water is caused by:","opts":["CaSO₄","MgSO₄","Ca(HCO₃)₂","CaCl₂"],"a":"Ca(HCO₃)₂","topic":"Water Treatment","unit":"Unit-4","diff":"easy"},
        {"type":"tf","q":"Reverse osmosis removes dissolved salts from water.","a":"True","topic":"Water Treatment","unit":"Unit-4","diff":"easy"},
        {"type":"mcq","q":"The process of removing hardness using lime-soda process converts Ca²⁺ to:","opts":["CaCl₂","CaSO₄","CaCO₃","Ca(OH)₂"],"a":"CaCO₃","topic":"Water Treatment","unit":"Unit-4","diff":"medium"},
        {"type":"mcq","q":"BOD stands for:","opts":["Biological Oxygen Demand","Biochemical Oxygen Deficiency","Basic Oxygen Demand","Biological Organic Decomposition"],"a":"Biological Oxygen Demand","topic":"Water Treatment","unit":"Unit-4","diff":"easy"},
    ],

    # ── EEE (Electrical & Electronics Engineering) ────────────────────────────
    "EEE": [
        # Unit 1 – DC Circuits
        {"type":"mcq","q":"Kirchhoff's Current Law (KCL) states that:","opts":["Sum of voltages in a loop is zero","Sum of currents entering a node equals sum leaving","Voltage is proportional to resistance","Power is voltage times current"],"a":"Sum of currents entering a node equals sum leaving","topic":"DC Circuits","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"In a series circuit, the total resistance is the sum of all individual resistances.","a":"True","topic":"DC Circuits","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"Thevenin's theorem replaces a complex network with:","opts":["A current source and parallel resistance","A voltage source and series resistance","A voltage source only","Two resistors in series"],"a":"A voltage source and series resistance","topic":"DC Circuits","unit":"Unit-1","diff":"medium"},
        {"type":"mcq","q":"The unit of electrical conductance is:","opts":["Ohm","Farad","Siemens","Henry"],"a":"Siemens","topic":"DC Circuits","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"Norton's theorem is the dual of Thevenin's theorem.","a":"True","topic":"DC Circuits","unit":"Unit-1","diff":"medium"},
        # Unit 2 – AC Circuits
        {"type":"mcq","q":"The impedance of a purely capacitive circuit is:","opts":["R","jωL","1/jωC","-jωC"],"a":"1/jωC","topic":"AC Circuits","unit":"Unit-2","diff":"medium"},
        {"type":"mcq","q":"Power factor is defined as:","opts":["Active power / Apparent power","Reactive power / Apparent power","Apparent power / Active power","Active power × Reactive power"],"a":"Active power / Apparent power","topic":"AC Circuits","unit":"Unit-2","diff":"medium"},
        {"type":"tf","q":"At resonance in a series RLC circuit, the impedance is purely resistive.","a":"True","topic":"AC Circuits","unit":"Unit-2","diff":"medium"},
        {"type":"mcq","q":"The RMS value of a sinusoidal voltage with peak value Vm is:","opts":["Vm","Vm/√2","Vm/2","Vm×√2"],"a":"Vm/√2","topic":"AC Circuits","unit":"Unit-2","diff":"easy"},
        # Unit 3 – Transformers & Machines
        {"type":"mcq","q":"The efficiency of a transformer is maximum when:","opts":["Iron loss = Copper loss","Iron loss > Copper loss","Copper loss > Iron loss","Iron loss = 0"],"a":"Iron loss = Copper loss","topic":"Transformers","unit":"Unit-3","diff":"medium"},
        {"type":"tf","q":"A transformer can work on DC supply.","a":"False","topic":"Transformers","unit":"Unit-3","diff":"easy"},
        {"type":"mcq","q":"In a DC motor, back EMF is:","opts":["Always greater than supply voltage","Equal to supply voltage","Always less than supply voltage","Zero at full load"],"a":"Always less than supply voltage","topic":"DC Machines","unit":"Unit-3","diff":"medium"},
        # Unit 4 – Semiconductors & Devices
        {"type":"mcq","q":"In a p-n junction diode under forward bias, the depletion region:","opts":["Widens","Narrows","Stays the same","Disappears completely"],"a":"Narrows","topic":"Semiconductors","unit":"Unit-4","diff":"easy"},
        {"type":"tf","q":"A Zener diode operates in the reverse breakdown region.","a":"True","topic":"Semiconductors","unit":"Unit-4","diff":"easy"},
        {"type":"mcq","q":"The transistor configuration with highest current gain is:","opts":["Common Base","Common Emitter","Common Collector","All equal"],"a":"Common Emitter","topic":"Semiconductors","unit":"Unit-4","diff":"medium"},
        {"type":"mcq","q":"Which logic gate produces output 1 only when all inputs are 1?","opts":["OR","NAND","AND","NOR"],"a":"AND","topic":"Digital Electronics","unit":"Unit-4","diff":"easy"},
        {"type":"tf","q":"NAND gate is a universal gate.","a":"True","topic":"Digital Electronics","unit":"Unit-4","diff":"easy"},
    ],

    # ── EPD (Engineering Physics / Design) ────────────────────────────────────
    "EPD": [
        # Unit 1 – Design Process
        {"type":"mcq","q":"Which stage of the engineering design process involves generating multiple solutions?","opts":["Define","Ideate","Prototype","Test"],"a":"Ideate","topic":"Design Process","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"Empathy mapping is used in the 'Define' stage of Design Thinking.","a":"False","topic":"Design Thinking","unit":"Unit-1","diff":"medium"},
        {"type":"mcq","q":"A Gantt chart is primarily used for:","opts":["Budget planning","Project scheduling","Risk analysis","Market research"],"a":"Project scheduling","topic":"Project Management","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"The iterative cycle of Design Thinking is:","opts":["Plan-Do-Check-Act","Empathize-Define-Ideate-Prototype-Test","Analysis-Design-Implement-Test","Research-Design-Build-Launch"],"a":"Empathize-Define-Ideate-Prototype-Test","topic":"Design Thinking","unit":"Unit-1","diff":"easy"},
        # Unit 2 – Engineering Drawing & CAD
        {"type":"mcq","q":"First angle projection is followed in:","opts":["USA","Japan","Europe and India","Australia"],"a":"Europe and India","topic":"Engineering Drawing","unit":"Unit-2","diff":"medium"},
        {"type":"tf","q":"In isometric projection, all three axes are equally inclined to each other at 120°.","a":"True","topic":"Engineering Drawing","unit":"Unit-2","diff":"medium"},
        {"type":"mcq","q":"A section view in engineering drawing is used to:","opts":["Show external features","Reveal internal features","Indicate surface finish","Show dimensions only"],"a":"Reveal internal features","topic":"Engineering Drawing","unit":"Unit-2","diff":"easy"},
        # Unit 3 – Materials Science
        {"type":"mcq","q":"The property of a material to withstand repeated loading without failure is called:","opts":["Hardness","Toughness","Fatigue strength","Creep resistance"],"a":"Fatigue strength","topic":"Materials","unit":"Unit-3","diff":"medium"},
        {"type":"tf","q":"Composites are made of two or more materials with different properties.","a":"True","topic":"Materials","unit":"Unit-3","diff":"easy"},
        {"type":"mcq","q":"Young's modulus is the ratio of:","opts":["Stress to strain","Strain to stress","Force to area","Deformation to length"],"a":"Stress to strain","topic":"Materials","unit":"Unit-3","diff":"easy"},
        # Unit 4 – Sustainability & Innovation
        {"type":"mcq","q":"Which of the following best describes sustainable engineering?","opts":["Maximising profit","Meeting present needs without compromising future generations","Using only renewable materials","Reducing workforce"],"a":"Meeting present needs without compromising future generations","topic":"Sustainability","unit":"Unit-4","diff":"easy"},
        {"type":"tf","q":"Life Cycle Assessment (LCA) evaluates the environmental impact of a product from cradle to grave.","a":"True","topic":"Sustainability","unit":"Unit-4","diff":"medium"},
        {"type":"mcq","q":"Intellectual Property Rights (IPR) for a new invention is protected by:","opts":["Copyright","Trademark","Patent","Trade Secret"],"a":"Patent","topic":"IPR","unit":"Unit-4","diff":"easy"},
    ],

    # ── EVS (Environmental Science) ───────────────────────────────────────────
    "EVS": [
        {"type":"mcq","q":"Which of the following is a greenhouse gas?","opts":["Nitrogen","Oxygen","Methane","Argon"],"a":"Methane","topic":"Climate Change","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"The ozone layer is located in the stratosphere.","a":"True","topic":"Atmosphere","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"Biodiversity hotspots are regions with:","opts":["Low species richness","High species richness and high threat","Only endemic species","No human population"],"a":"High species richness and high threat","topic":"Biodiversity","unit":"Unit-2","diff":"medium"},
        {"type":"tf","q":"Eutrophication is caused by excess nutrients in water bodies.","a":"True","topic":"Water Pollution","unit":"Unit-2","diff":"easy"},
        {"type":"mcq","q":"Which renewable energy source has the highest global installed capacity?","opts":["Solar","Wind","Hydropower","Geothermal"],"a":"Hydropower","topic":"Energy","unit":"Unit-3","diff":"hard"},
        {"type":"mcq","q":"The Rio Earth Summit took place in:","opts":["1972","1987","1992","2002"],"a":"1992","topic":"Environment Policy","unit":"Unit-3","diff":"medium"},
        {"type":"tf","q":"The full form of EIA is Environmental Impact Assessment.","a":"True","topic":"Environment Policy","unit":"Unit-3","diff":"easy"},
        {"type":"mcq","q":"Which article of the Indian Constitution relates to protection of environment?","opts":["Article 21","Article 48A","Article 51A(g)","Both 48A and 51A(g)"],"a":"Both 48A and 51A(g)","topic":"Environment Law","unit":"Unit-4","diff":"hard"},
        {"type":"mcq","q":"The primary cause of soil erosion is:","opts":["Afforestation","Deforestation","Crop rotation","Contour farming"],"a":"Deforestation","topic":"Soil","unit":"Unit-4","diff":"easy"},
        {"type":"tf","q":"Carbon dioxide is the most potent greenhouse gas by global warming potential.","a":"False","topic":"Climate Change","unit":"Unit-1","diff":"medium"},
        {"type":"mcq","q":"Which of these is a non-renewable resource?","opts":["Solar energy","Wind","Coal","Tidal energy"],"a":"Coal","topic":"Resources","unit":"Unit-3","diff":"easy"},
        {"type":"mcq","q":"The Kyoto Protocol aimed to reduce emissions of:","opts":["Nitrogen","Greenhouse gases","Sulphur dioxide","CFCs"],"a":"Greenhouse gases","topic":"Environment Policy","unit":"Unit-3","diff":"medium"},
    ],

    # ── MES (Mechanical Engineering Science) ──────────────────────────────────
    "MES": [
        {"type":"mcq","q":"The first law of thermodynamics is a statement of:","opts":["Conservation of momentum","Conservation of mass","Conservation of energy","Conservation of entropy"],"a":"Conservation of energy","topic":"Thermodynamics","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"An adiabatic process occurs without heat transfer between system and surroundings.","a":"True","topic":"Thermodynamics","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"The efficiency of a Carnot engine operating between temperatures T₁ and T₂ (T₁ > T₂) is:","opts":["1 - T₁/T₂","T₂/T₁","1 - T₂/T₁","T₁/T₂"],"a":"1 - T₂/T₁","topic":"Thermodynamics","unit":"Unit-1","diff":"medium"},
        {"type":"mcq","q":"In which thermodynamic process does pressure remain constant?","opts":["Isothermal","Adiabatic","Isobaric","Isochoric"],"a":"Isobaric","topic":"Thermodynamics","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"Entropy of a system always decreases in an irreversible process.","a":"False","topic":"Thermodynamics","unit":"Unit-1","diff":"medium"},
        # Unit 2 – Fluid Mechanics
        {"type":"mcq","q":"Bernoulli's equation is based on the principle of:","opts":["Conservation of mass","Conservation of momentum","Conservation of energy","Newton's second law"],"a":"Conservation of energy","topic":"Fluid Mechanics","unit":"Unit-2","diff":"easy"},
        {"type":"tf","q":"Viscosity of a liquid increases with temperature.","a":"False","topic":"Fluid Mechanics","unit":"Unit-2","diff":"medium"},
        {"type":"mcq","q":"Reynolds number is the ratio of:","opts":["Inertia forces to viscous forces","Viscous forces to gravity","Pressure to velocity","Density to viscosity"],"a":"Inertia forces to viscous forces","topic":"Fluid Mechanics","unit":"Unit-2","diff":"medium"},
        # Unit 3 – Manufacturing
        {"type":"mcq","q":"Which manufacturing process uses molten metal poured into a mould?","opts":["Forging","Casting","Rolling","Extrusion"],"a":"Casting","topic":"Manufacturing","unit":"Unit-3","diff":"easy"},
        {"type":"tf","q":"Turning is a material removal process performed on a lathe.","a":"True","topic":"Manufacturing","unit":"Unit-3","diff":"easy"},
        {"type":"mcq","q":"The tolerance in manufacturing refers to:","opts":["Material strength","Permissible variation in dimensions","Surface finish grade","Type of fit"],"a":"Permissible variation in dimensions","topic":"Manufacturing","unit":"Unit-3","diff":"medium"},
        # Unit 4 – Machine Elements
        {"type":"mcq","q":"Which type of gear is used to transmit motion between parallel shafts?","opts":["Bevel gear","Worm gear","Spur gear","Helical gear (crossed)"],"a":"Spur gear","topic":"Machine Elements","unit":"Unit-4","diff":"easy"},
        {"type":"tf","q":"A bearing is used to reduce friction between rotating and stationary parts.","a":"True","topic":"Machine Elements","unit":"Unit-4","diff":"easy"},
        {"type":"mcq","q":"The modulus of rigidity relates shear stress to:","opts":["Normal strain","Shear strain","Volumetric strain","Lateral strain"],"a":"Shear strain","topic":"Strength of Materials","unit":"Unit-4","diff":"medium"},
    ],

    # ── PHYSICS ───────────────────────────────────────────────────────────────
    "Physics": [
        # Unit 1 – Oscillations & Waves
        {"type":"mcq","q":"The time period of a simple pendulum depends on:","opts":["Mass of bob","Amplitude","Length and g","Length only"],"a":"Length and g","topic":"Oscillations","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"In simple harmonic motion, acceleration is proportional to displacement and directed towards equilibrium.","a":"True","topic":"Oscillations","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"The phenomenon of beats is produced by superposition of two waves with:","opts":["Same frequency","Different amplitudes only","Slightly different frequencies","90° phase difference"],"a":"Slightly different frequencies","topic":"Waves","unit":"Unit-1","diff":"medium"},
        # Unit 2 – Optics
        {"type":"mcq","q":"Which condition is required for total internal reflection?","opts":["Light going from denser to rarer medium at angle > critical angle","Light going from rarer to denser medium","Any angle of incidence","Equal refractive indices"],"a":"Light going from denser to rarer medium at angle > critical angle","topic":"Optics","unit":"Unit-2","diff":"medium"},
        {"type":"tf","q":"In Young's double slit experiment, fringe width is directly proportional to wavelength.","a":"True","topic":"Optics","unit":"Unit-2","diff":"medium"},
        {"type":"mcq","q":"The resolving power of a microscope increases with:","opts":["Increasing wavelength","Decreasing numerical aperture","Decreasing wavelength","Increasing focal length"],"a":"Decreasing wavelength","topic":"Optics","unit":"Unit-2","diff":"hard"},
        # Unit 3 – Quantum Mechanics
        {"type":"mcq","q":"The de Broglie wavelength of a particle is given by:","opts":["λ = h/mv","λ = mv/h","λ = hm/v","λ = h×mv"],"a":"λ = h/mv","topic":"Quantum Mechanics","unit":"Unit-3","diff":"medium"},
        {"type":"tf","q":"Heisenberg's uncertainty principle states that position and momentum cannot both be precisely known simultaneously.","a":"True","topic":"Quantum Mechanics","unit":"Unit-3","diff":"easy"},
        {"type":"mcq","q":"The photoelectric effect proves that light has:","opts":["Wave nature","Particle nature","Neither","Both wave and particle nature"],"a":"Particle nature","topic":"Quantum Mechanics","unit":"Unit-3","diff":"medium"},
        # Unit 4 – Lasers & Fibre Optics
        {"type":"mcq","q":"LASER stands for:","opts":["Light Amplification by Stimulated Emission of Radiation","Light Absorption by Stimulated Emission of Radiation","Light Amplification by Spontaneous Emission of Radiation","None of the above"],"a":"Light Amplification by Stimulated Emission of Radiation","topic":"Lasers","unit":"Unit-4","diff":"easy"},
        {"type":"tf","q":"In optical fibre, light travels by the principle of total internal reflection.","a":"True","topic":"Fibre Optics","unit":"Unit-4","diff":"easy"},
        {"type":"mcq","q":"Population inversion is necessary for:","opts":["Photoelectric effect","Laser action","Diffraction","Interference"],"a":"Laser action","topic":"Lasers","unit":"Unit-4","diff":"medium"},
        {"type":"mcq","q":"The numerical aperture of an optical fibre determines its:","opts":["Refractive index","Light-gathering ability","Wavelength of light","Length of fibre"],"a":"Light-gathering ability","topic":"Fibre Optics","unit":"Unit-4","diff":"medium"},
    ],

    # ── PYTHON ────────────────────────────────────────────────────────────────
    "Python": [
        {"type":"mcq","q":"What is the output of: `print(type([]))`?","opts":["<class 'tuple'>","<class 'list'>","<class 'array'>","<class 'dict'>"],"a":"<class 'list'>","topic":"Data Types","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"Python lists are mutable but tuples are immutable.","a":"True","topic":"Data Types","unit":"Unit-1","diff":"easy"},
        {"type":"code","q":"```python\nx = [1, 2, 3, 4, 5]\nprint(x[1:4])\n```\nWhat is the output?","opts":["[1, 2, 3]","[2, 3, 4]","[1, 2, 3, 4]","[2, 3, 4, 5]"],"a":"[2, 3, 4]","topic":"Lists","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"Which keyword is used to define a function in Python?","opts":["function","def","fun","define"],"a":"def","topic":"Functions","unit":"Unit-2","diff":"easy"},
        {"type":"tf","q":"In Python, indentation is optional and only used for readability.","a":"False","topic":"Syntax","unit":"Unit-1","diff":"easy"},
        {"type":"code","q":"```python\ndef fact(n):\n    if n == 0: return 1\n    return n * fact(n-1)\nprint(fact(4))\n```\nWhat does this print?","opts":["4","16","24","12"],"a":"24","topic":"Recursion","unit":"Unit-2","diff":"medium"},
        {"type":"mcq","q":"What does the `len()` function return for a string 'hello'?","opts":["4","5","6","TypeError"],"a":"5","topic":"Strings","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"Which of the following is used to handle exceptions in Python?","opts":["try-catch","try-except","if-else","do-while"],"a":"try-except","topic":"Exception Handling","unit":"Unit-3","diff":"easy"},
        {"type":"tf","q":"A Python dictionary can have duplicate keys.","a":"False","topic":"Data Types","unit":"Unit-2","diff":"easy"},
        {"type":"code","q":"```python\nd = {'a': 1, 'b': 2}\nd['c'] = 3\nprint(len(d))\n```\nWhat is printed?","opts":["2","3","4","Error"],"a":"3","topic":"Dictionaries","unit":"Unit-2","diff":"easy"},
        {"type":"mcq","q":"What is the time complexity of searching in a Python dictionary (average case)?","opts":["O(n)","O(log n)","O(1)","O(n²)"],"a":"O(1)","topic":"Complexity","unit":"Unit-4","diff":"medium"},
        {"type":"mcq","q":"Which method removes and returns the last element of a list?","opts":[".remove()","-.pop()","del","discard()"],"a":"-.pop()","topic":"Lists","unit":"Unit-2","diff":"easy"},
        {"type":"tf","q":"Python supports multiple inheritance.","a":"True","topic":"OOP","unit":"Unit-3","diff":"medium"},
        {"type":"code","q":"```python\nfor i in range(3):\n    print(i, end=' ')\n```\nWhat is the output?","opts":["1 2 3","0 1 2","0 1 2 3","0 1"],"a":"0 1 2","topic":"Loops","unit":"Unit-2","diff":"easy"},
        {"type":"mcq","q":"Which of the following creates a shallow copy of a list `a`?","opts":["b = a","b = a.copy()","b = list(a)","Both b and c"],"a":"Both b and c","topic":"Lists","unit":"Unit-2","diff":"medium"},
    ],

    # ── STATICS ───────────────────────────────────────────────────────────────
    "Statics": [
        {"type":"mcq","q":"A body is in static equilibrium when the net force and net moment acting on it are:","opts":["Maximum","Minimum","Zero","Equal"],"a":"Zero","topic":"Equilibrium","unit":"Unit-1","diff":"easy"},
        {"type":"tf","q":"Lami's theorem applies to a body in equilibrium under exactly three concurrent forces.","a":"True","topic":"Equilibrium","unit":"Unit-1","diff":"medium"},
        {"type":"mcq","q":"The moment of a force about a point is equal to:","opts":["Force × distance","Force + distance","Force / distance","Force × cos θ"],"a":"Force × distance","topic":"Moments","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"The resultant of two forces P and Q at angle θ is:","opts":["P + Q","√(P² + Q² + 2PQ cosθ)","√(P² + Q² - 2PQ cosθ)","P - Q"],"a":"√(P² + Q² + 2PQ cosθ)","topic":"Forces","unit":"Unit-1","diff":"medium"},
        {"type":"tf","q":"A couple has a net resultant force of zero.","a":"True","topic":"Moments","unit":"Unit-1","diff":"easy"},
        {"type":"mcq","q":"Centre of gravity of a uniform semicircular lamina from the diameter is:","opts":["r/2","4r/3π","r/π","2r/π"],"a":"4r/3π","topic":"Centroid","unit":"Unit-2","diff":"hard"},
        {"type":"mcq","q":"The centroid of a triangle lies at:","opts":["1/2 of height","1/3 of height from base","2/3 of height from base","At the midpoint of each side"],"a":"1/3 of height from base","topic":"Centroid","unit":"Unit-2","diff":"medium"},
        {"type":"tf","q":"The moment of inertia of a body depends on the axis of rotation.","a":"True","topic":"Moment of Inertia","unit":"Unit-3","diff":"easy"},
        {"type":"mcq","q":"The parallel axis theorem states: I = Iₐ + ___","opts":["Mr","Mr²","M/r²","Iₐ/M"],"a":"Mr²","topic":"Moment of Inertia","unit":"Unit-3","diff":"medium"},
        {"type":"mcq","q":"A truss is said to be statically determinate when:","opts":["m = 2j","m = 2j - 3","m + r = 2j","m = j + 3"],"a":"m + r = 2j","topic":"Trusses","unit":"Unit-4","diff":"hard"},
        {"type":"tf","q":"In the method of sections, we cut through the truss and apply equilibrium to one part.","a":"True","topic":"Trusses","unit":"Unit-4","diff":"medium"},
        {"type":"mcq","q":"Friction force is always:","opts":["Perpendicular to the contact surface","Parallel to and opposing relative motion","Equal to normal reaction","In the direction of motion"],"a":"Parallel to and opposing relative motion","topic":"Friction","unit":"Unit-4","diff":"easy"},
        {"type":"mcq","q":"The angle of friction is defined as:","opts":["tan⁻¹(μ)","sin⁻¹(μ)","cos⁻¹(μ)","μ itself"],"a":"tan⁻¹(μ)","topic":"Friction","unit":"Unit-4","diff":"medium"},
        {"type":"tf","q":"Static friction is always greater than or equal to kinetic friction.","a":"True","topic":"Friction","unit":"Unit-4","diff":"easy"},
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _make(qtype, text, opts, answer, topic, subject, unit, diff) -> dict:
    return {
        "question_id":    str(uuid.uuid4()),
        "question_type":  qtype,
        "question_text":  text,
        "options":        opts,
        "correct_answer": answer,
        "topic":          topic,
        "subject":        subject,
        "unit":           unit,
        "difficulty_level": diff,
    }


def _bank_to_questions(subject: str) -> list[dict]:
    """Convert raw bank entries into proper question dicts."""
    out = []
    for entry in SUBJECT_BANKS.get(subject, []):
        q = _make(
            qtype   = entry["type"],
            text    = entry["q"],
            opts    = entry.get("opts"),
            answer  = entry["a"],
            topic   = entry["topic"],
            subject = subject,
            unit    = entry.get("unit", ""),
            diff    = entry["diff"],
        )
        out.append(q)
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def get_all_preloaded_questions() -> list[dict]:
    """Return every question from all 8 subject banks."""
    all_qs = []
    for subject in SUBJECT_BANKS:
        all_qs.extend(_bank_to_questions(subject))
    return all_qs


def get_questions_for_subject(subject: str) -> list[dict]:
    return _bank_to_questions(subject)


def generate_questions(text: str, num_questions: int = 10, difficulty: str = "medium",
                       subject: str = "General") -> list[dict]:
    """
    Generate questions from free text (for uploaded files).
    Falls back to pre-loaded bank if subject matches.
    """
    from parser import extract_key_terms

    # If the subject matches a known bank, supplement from there
    if subject in SUBJECT_BANKS:
        bank = _bank_to_questions(subject)
        pool = [q for q in bank if q["difficulty_level"] == difficulty]
        if not pool:
            pool = bank
        random.shuffle(pool)
        # Re-assign fresh UUIDs so they're unique inserts
        chosen = []
        for q in pool[:num_questions]:
            q2 = dict(q)
            q2["question_id"] = str(uuid.uuid4())
            chosen.append(q2)
        return chosen

    # Generic generation from text
    key_terms = extract_key_terms(text)
    questions = []

    tf_facts = _extract_tf_from_text(text)
    for fact, answer in tf_facts[:max(num_questions // 3, 2)]:
        questions.append(_make("true_false", fact, ["True", "False"], str(answer),
                               key_terms[0] if key_terms else "General",
                               subject, "", difficulty))

    for term in key_terms[:num_questions - len(questions)]:
        questions.append(_make(
            "mcq",
            f"Which of the following best describes '{term}'?",
            [f"A concept related to {term}",
             f"Unrelated to {term}",
             f"The opposite of {term}",
             f"A subset of {term}"],
            f"A concept related to {term}",
            term, subject, "", difficulty,
        ))

    random.shuffle(questions)
    return questions[:num_questions]


def _extract_tf_from_text(text: str) -> list[tuple[str, bool]]:
    """Heuristically extract potential true/false statements from text."""
    sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if len(s.strip()) > 20]
    facts = []
    for s in sentences[:20]:
        if any(kw in s.lower() for kw in ["is", "are", "always", "never", "defined", "called", "known"]):
            facts.append((s + ".", True))
    return facts[:6]