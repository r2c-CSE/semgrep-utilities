// Code for SBT Command dependencyTreeTransform to transform the dependency Tree and write to maven_dep_tree txt file
import scala.sys.process._

val dependencyTreeTransform = taskKey[Unit]("Transforms the output of the dependencyTree command")

dependencyTreeTransform := {
  val logger = streams.value.log

  // Execute 'sbt dependencyTree' and capture the output as a string
  val output = Process(Seq("sbt", "dependencyTree")).!!
  
  // Process the output as done in your Python script
  val relevantLines = output.split("\n")
                              .dropWhile(!_.contains("set current project to"))
                              .drop(1)
                              .filterNot(_.trim.startsWith("[success]"))
                              .filter(_.trim.nonEmpty)

  val transformedLines = relevantLines.map { line =>
  line.replace("[info]", "").replace("[S]", "").trim
}.filterNot { line =>
  line.matches("^[ |]+$") || line.isEmpty
}.filterNot{ line => 
  line.matches(".+evicted by: .+")
}.map { line =>
  val parts = line.split(':')
  val formattedLine = if (parts.length > 2) {
    (parts.take(2) :+ "jar" :+ parts(2) :+ "compile").mkString(":")
  } else {
    line
  }
  // Ensure there is appropriate spacing for pipes and +- 
  formattedLine.replaceAll("\\+-", "+- ")
  formattedLine.replaceAll("\\|\\s+", "|  ")
}

  // Write the transformed lines to a file
  val file = new java.io.File("maven_dep_tree.txt")
  val pw = new java.io.PrintWriter(file)
  try transformedLines.foreach(pw.println)
  finally pw.close()
}
