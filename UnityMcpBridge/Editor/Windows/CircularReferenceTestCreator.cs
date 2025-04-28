using UnityEngine;
using UnityEditor;
using System.Collections.Generic;

namespace UnityMcpBridge.Editor.Windows
{
    /// <summary>
    /// Helper class to create test scenes with circular references for testing
    /// the serialization system's circular reference detection.
    /// </summary>
    public static class CircularReferenceTestCreator
    {
        [MenuItem("Tools/Unity MCP/Create Circular Reference Test")]
        public static void CreateCircularReferenceTest()
        {
            // Create a parent GameObject
            var parent = new GameObject("CircularRefParent");
            
            // Create a child GameObject
            var child = new GameObject("CircularRefChild");
            child.transform.SetParent(parent.transform);
            
            // Create another child for nested references
            var grandchild = new GameObject("CircularRefGrandchild");
            grandchild.transform.SetParent(child.transform);
            
            // Add components with circular references
            var parentComponent = parent.AddComponent<CircularRefParentComponent>();
            var childComponent = child.AddComponent<CircularRefChildComponent>();
            var grandchildComponent = grandchild.AddComponent<CircularRefGrandchildComponent>();
            
            // Create circular references
            parentComponent.ChildComponent = childComponent;
            childComponent.ParentComponent = parentComponent;
            childComponent.GrandchildComponent = grandchildComponent;
            grandchildComponent.ParentComponent = parentComponent; // Creates a triangle of references
            
            // Create a self-referencing object
            var selfRef = new GameObject("SelfReferenceObject");
            var selfRefComponent = selfRef.AddComponent<SelfReferencingComponent>();
            selfRefComponent.SelfReference = selfRefComponent;
            
            // Create circular reference through a collection
            var collectionHolder = new GameObject("CollectionHolder");
            var collectionComponent = collectionHolder.AddComponent<CollectionRefComponent>();
            collectionComponent.ReferencedObjects = new List<GameObject> { parent, child, collectionHolder };
            
            // Create a circular reference across a deeper object graph
            var complexRefA = new GameObject("ComplexRefA");
            var complexRefB = new GameObject("ComplexRefB");
            var complexRefC = new GameObject("ComplexRefC");
            
            var compA = complexRefA.AddComponent<ComplexRefComponent>();
            var compB = complexRefB.AddComponent<ComplexRefComponent>();
            var compC = complexRefC.AddComponent<ComplexRefComponent>();
            
            compA.NextComponent = compB;
            compB.NextComponent = compC;
            compC.NextComponent = compA; // Circular reference in a chain
            
            Debug.Log("Created test GameObjects with circular references.");
            Debug.Log("Use the SerializationTestWindow to test serialization with these objects.");
        }
        
        // Test helper scripts
        
        public class CircularRefParentComponent : MonoBehaviour
        {
            public CircularRefChildComponent ChildComponent;
        }
        
        public class CircularRefChildComponent : MonoBehaviour
        {
            public CircularRefParentComponent ParentComponent;
            public CircularRefGrandchildComponent GrandchildComponent;
        }
        
        public class CircularRefGrandchildComponent : MonoBehaviour
        {
            public CircularRefParentComponent ParentComponent;
        }
        
        public class SelfReferencingComponent : MonoBehaviour
        {
            public SelfReferencingComponent SelfReference;
        }
        
        public class CollectionRefComponent : MonoBehaviour
        {
            public List<GameObject> ReferencedObjects;
        }
        
        public class ComplexRefComponent : MonoBehaviour
        {
            public ComplexRefComponent NextComponent;
        }
    }
} 