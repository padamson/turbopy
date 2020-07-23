# Computational Physics Simulation Framework
#
# Based on the structure of turboWAVE
#
import numpy as np

from .core import Diagnostic, Simulation


class CSVOutputUtility:
    def __init__(self, filename, diagnostic_size):
        self.filename = filename
        self.buffer = np.zeros(diagnostic_size)
        self.buffer_index = 0
        
    def append(self, data):
        self.buffer[self.buffer_index, :] = data
        self.buffer_index += 1
    
    def finalize(self):
        with open(self.filename, 'wb') as f:
            np.savetxt(f, self.buffer, delimiter=",")


class PointDiagnostic(Diagnostic):
    def __init__(self, owner: Simulation, input_data: dict):
        super().__init__(owner, input_data)
        self.location = input_data["location"]
        self.field_name = input_data["field"]
        self.output = input_data["output_type"] # "stdout"
        self.get_value = None
        self.field = None
        self.output_function = None
        self.csv = None
                
    def diagnose(self):
        self.output_function(self.get_value(self.field))

    def inspect_resource(self, resource):
        if self.field_name in resource:
            self.field = resource[self.field_name]

    def print_diagnose(self, data):
        print(data)
        
    def initialize(self):
        # set up function to interpolate the field value
        self.get_value = self.owner.grid.create_interpolator(self.location)
        
        # setup output method
        functions = {"stdout": self.print_diagnose,
                     "csv": self.csv_diagnose,
                     }
        self.output_function = functions[self.input_data["output_type"]]

        if self.input_data["output_type"] == "csv":
            diagnostic_size = (self.owner.clock.num_steps + 1, 1)
            self.csv = CSVOutputUtility(self.input_data["filename"], diagnostic_size)

    def csv_diagnose(self, data):
        self.csv.append(data)

    def finalize(self):
        self.diagnose()
        if self.input_data["output_type"] == "csv":
            self.csv.finalize()


class FieldDiagnostic(Diagnostic):
    def __init__(self, owner: Simulation, input_data: dict):
        super().__init__(owner, input_data)
        
        self.component = input_data["component"]
        self.field_name = input_data["field"]
        self.output = input_data["output_type"] # "stdout"
        self.field = None

        self.dump_interval = None
        self.last_dump = None
        self.diagnose = self.do_diagnostic
        self.diagnostic_size = None
        
        self.field_was_found = False

    def check_step(self):
        if self.owner.clock.time >= self.last_dump + self.dump_interval:
            self.do_diagnostic()
            self.last_dump = self.owner.clock.time
    
    def do_diagnostic(self):
        if len(self.field.shape) > 1:
            self.output_function(self.field[:, self.component])
        else:
            self.output_function(self.field)

    def inspect_resource(self, resource):
        if self.field_name in resource:
            self.field_was_found = True
            self.field = resource[self.field_name]
    
    def print_diagnose(self, data):
        print(self.field_name, data)
        
    def initialize(self):
        if not self.field_was_found:
            raise(RuntimeError(f"Diagnostic field {self.field_name} was not found"))
        self.diagnostic_size = (self.owner.clock.num_steps+1,
                                self.owner.grid.num_points)
        if "dump_interval" in self.input_data:
            self.dump_interval = self.input_data["dump_interval"]
            self.diagnose = self.check_step
            self.last_dump = 0
            self.diagnostic_size = (int(np.ceil(self.owner.clock.end_time/self.dump_interval)+1),
                                    self.owner.grid.num_points)       
    
        # setup output method
        functions = {"stdout": self.print_diagnose,
                     "csv": self.csv_diagnose,
                     }
        self.output_function = functions[self.input_data["output_type"]]
        if self.input_data["output_type"] == "csv":
            self.csv = CSVOutputUtility(self.input_data["filename"], self.diagnostic_size)
    
    def csv_diagnose(self, data):
        self.csv.append(data)
    
    def finalize(self):
        self.do_diagnostic()
        if self.input_data["output_type"] == "csv":
            self.csv.finalize()


class GridDiagnostic(Diagnostic):
    def __init__(self, owner: Simulation, input_data: dict):
        super().__init__(owner, input_data)
        self.filename = input_data["filename"]
            
    def diagnose(self):
        pass

    def initialize(self):
        with open(self.filename, 'wb') as f:
            np.savetxt(f, self.owner.grid.r, delimiter=",")

    def finalize(self):
        pass


class ClockDiagnostic(Diagnostic):
    def __init__(self, owner: Simulation, input_data: dict):
        super().__init__(owner, input_data)
        self.filename = input_data["filename"]
        self.csv = None

    def diagnose(self):
        self.csv.append(self.owner.clock.time)

    def initialize(self):
        diagnostic_size = (self.owner.clock.num_steps + 1, 1)
        self.csv = CSVOutputUtility(self.input_data["filename"], diagnostic_size)

    def finalize(self):
        self.diagnose()
        self.csv.finalize()


Diagnostic.register("point", PointDiagnostic)
Diagnostic.register("field", FieldDiagnostic)
Diagnostic.register("grid", GridDiagnostic)
Diagnostic.register("clock", ClockDiagnostic)

