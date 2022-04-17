#!/usr/bin/env kotlin

@file:DependsOn("com.google.cloud:google-cloud-firestore:1.32.0")
@file:DependsOn("org.jetbrains.kotlinx:kotlinx-serialization-json-jvm:1.3.2")
@file:Suppress("UNCHECKED_CAST", "RECEIVER_NULLABILITY_MISMATCH_BASED_ON_JAVA_ANNOTATIONS")

import com.google.auth.oauth2.GoogleCredentials
import com.google.cloud.firestore.CollectionReference
import com.google.cloud.firestore.DocumentReference
import com.google.cloud.firestore.FirestoreOptions
import com.google.cloud.firestore.WriteBatch
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import java.io.File
import java.io.FileInputStream

var db = FirestoreOptions.newBuilder()
  .setCredentials(
    GoogleCredentials.fromStream(FileInputStream(File("serviceAccount.json")))
  )
  .build()
  .service

if (args.size == 0) {
  error("Usage: copy-data.main.kts [files to upload]")
}

args.map { File(it) }
  .forEach {
    val data = Json.parseToJsonElement(it.readText()).toAny()

    val batch = db.batch()
    writeCollection(data as Map<String, Any?>, batch, db.collection(it.nameWithoutExtension))
    val results = batch.commit().get()

    println("Updated ${it.name}: ${results.size} documents set")
  }

fun writeCollection(data: Map<String, Any?>, batch: WriteBatch, collectionReference: CollectionReference) {
  data.forEach {
    val value = it.value
    batch.set(
      collectionReference.document(it.key),
      walkDocument(value, batch, collectionReference.document(it.key))
    )
  }
}

fun String.isCollectionKey() = endsWith("-firestoreCollection")
fun String.collectionKey() = substringBeforeLast("-firestoreCollection")

fun walkDocument(data: Any?, batch: WriteBatch, documentReference: DocumentReference): Any {
  return when (data) {
    null -> error("Cannot write null document")
    is Map<*, *> -> {
      // The document is a map. Look inside to see if it contains collections
      data as Map<String, Any?>

      data.filterKeys { it.isCollectionKey() }.forEach {
        writeCollection(it.value as Map<String, Any?>, batch, documentReference.collection(it.key.collectionKey()))
      }
      return data.filterKeys { !it.isCollectionKey() }
    }
    else -> data
  }
}

fun JsonElement.toAny(): Any? {
  return when (this) {
    is JsonArray -> jsonArray.map { it.toAny() }
    is JsonObject -> jsonObject.mapValues { it.value.toAny() }
    is JsonNull -> null
    is JsonPrimitive -> when {
      this.jsonPrimitive.isString -> this.jsonPrimitive.content
      else -> booleanOrNull ?: intOrNull ?: longOrNull ?: doubleOrNull ?: content
    }
  }
}
